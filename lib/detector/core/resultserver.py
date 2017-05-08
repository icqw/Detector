import os
import socket
import select
import logging
import datetime
import SocketServer
from threading import Event, Thread

from lib.detector.common.utils import create_folder, Singleton
from lib.detector.common.config import Config
from lib.detector.common.exceptions import DetectorOperationalError
from lib.detector.common.exceptions import DetectorCriticalError
from lib.detector.common.exceptions import DetectorResultError

log = logging.getLogger(__name__)
BUFSIZE = 16 * 1024

class Disconnect(Exception):
    pass



class ResultServer(SocketServer.ThreadingTCPServer, object):
    """Result server. Singleton!

    This class handles results coming back from the analysis machines.
    """

    __metaclass__ = Singleton

    allow_reuse_address = True
    daemon_threads = True

    def __init__(self, *args, **kwargs):
        self.cfg = Config()
        self.analysistasks = {}
        self.analysishandlers = {}

        ip = self.cfg.resultserver.ip
        self.port = int(self.cfg.resultserver.port)

        while True:
            try:
                server_addr = ip, self.port
                SocketServer.ThreadingTCPServer.__init__(self,server_addr,ResultHandler,*args,**kwargs)
            except Exception as e:
                # In Linux /usr/include/asm-generic/errno-base.h.
                # EADDRINUSE  98 (Address already in use)
                # In Mac OS X or FreeBSD:
                # EADDRINUSE 48 (Address already in use)
                if e.errno == 98 or e.errno == 48:
                    log.warning("Cannot bind ResultServer on port %s, "
                                "trying another port.", self.port)
                    self.port += 1
                else:
                    raise DetectorCriticalError("Unable to bind ResultServer on "
                                              "{0}:{1}: {2}".format(
                                                  ip, self.port, str(e)))
            else:
                log.debug("ResultServer running on %s:%s.", ip, self.port)
                self.servethread = Thread(target=self.serve_forever)
                self.servethread.setDaemon(True)
                self.servethread.start()
                break



class ResultHandler(SocketServer.BaseRequestHandler):
    """Result handler.

    This handler speaks our analysis log network protocol.
    """
    def setup(self):
        self.rawlogfd = None
        self.protocol = None
        self.startbuf = ""
        self.end_request = Event()
        self.done_event = Event()
        self.pid, self.ppid, self.procname = None, None, None
        self.server.register_handler(self)

    def finish(self):
        self.done_event.set()

        if self.protocol:
            self.protocol.close()
        if self.rawlogfd:
            self.rawlogfd.close()

    def wait_sock_or_end(self):
        while True:
            if self.end_request.isSet():
                return False
            rs, _, _ = select.select([self.request], [], [], 1)
            if rs:
                return True

    def seek(self, pos):
        pass

    def read(self, length):
        buf = ""
        while len(buf) < length:
            if not self.wait_sock_or_end():
                raise Disconnect()
            tmp = self.request.recv(length-len(buf))
            if not tmp:
                raise Disconnect()
            buf += tmp


        return buf

    def read_any(self):
        if not self.wait_sock_or_end():
            raise Disconnect()
        tmp = self.request.recv(BUFSIZE)
        if not tmp:
            raise Disconnect()
        return tmp

    def read_newline(self):
        buf = ""
        while "\n" not in buf:
            buf += self.read(1)
        return buf

    def negotiate_protocol(self):
        # Read until newline.
        buf = self.read_newline()


    def handle(self):
        ip, port = self.client_address
        self.connect_time = datetime.datetime.now()

        self.storagepath = self.server.build_storage_path(ip)
        if not self.storagepath:
            return

        # Create all missing folders for this analysis.
        self.create_folders()



        log.debug("Connection closed: {0}:{1}".format(ip, port))

    def open_process_log(self, event):
        pid = event["pid"]
        ppid = event["ppid"]
        procname = event["process_name"]

        if self.pid is not None:
            log.debug("ResultServer got a new process message but already "
                      "has pid %d ppid %s procname %s.",
                      pid, str(ppid), procname)
            raise DetectorResultError("ResultServer connection state "
                                    "inconsistent.")

        # Only report this process when we're tracking it.
        if event["track"]:
            log.debug("New process (pid=%s, ppid=%s, name=%s)",
                      pid, ppid, procname)

        path = os.path.join(self.storagepath, "logs", str(pid) + ".bson")
        self.rawlogfd = open(path, "wb")
        self.rawlogfd.write(self.startbuf)

        self.pid, self.ppid, self.procname = pid, ppid, procname

    def create_folders(self):
        folders = "shots", "files", "logs", "buffer"

        for folder in folders:
            try:
                create_folder(self.storagepath, folder=folder)
            except DetectorOperationalError:
                log.error("Unable to create folder %s" % folder)
                return False

