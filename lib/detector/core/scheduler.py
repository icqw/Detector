import os
import time
import shutil
import logging
import threading
import Queue

from lib.detector.common.config import Config#, parse_options, emit_options
from lib.detector.common.constants import DETECTOR_ROOT
from lib.detector.common.exceptions import DetectorMachineError, DetectorGuestError
from lib.detector.common.exceptions import DetectorOperationalError
from lib.detector.common.exceptions import DetectorCriticalError
#from lib.detector.common.objects import File
#from lib.detector.common.utils import create_folder
#from lib.detector.core.database import Database, TASK_COMPLETED, TASK_REPORTED
#from lib.detector.core.guest import GuestManager
#from lib.detector.core.plugins import list_plugins, RunAuxiliary, RunProcessing
#from lib.detector.core.plugins import RunSignatures, RunReporting
from lib.detector.core.resultserver import ResultServer


log = logging.getLogger(__name__)

machinery = None
machine_lock = None
latest_symlink_lock = threading.Lock()

active_analysis_count = 0


class Scheduler(object):
    """Tasks Scheduler.

    This class is responsible for the main execution loop of the tool. It
    prepares the analysis machines and keep waiting and loading for new
    analysis tasks.
    Whenever a new task is available, it launches AnalysisManager which will
    take care of running the full analysis process and operating with the
    assigned analysis machine.
    """
    def __init__(self, maxcount=None):
        self.running = True
        self.cfg = Config()
        self.db = Database()
        self.maxcount = maxcount
        self.total_analysis_count = 0

    def initialize(self):
        """Initialize the machine manager."""
        global machinery, machine_lock

        machinery_name = self.cfg.detector.machinery

        max_vmstartup_count = self.cfg.detector.max_vmstartup_count
        if max_vmstartup_count:
            machine_lock = threading.Semaphore(max_vmstartup_count)
        else:
            machine_lock = threading.Lock()

        log.info("Using \"%s\" as machine manager", machinery_name)

        # Get registered class name. Only one machine manager is imported,
        # therefore there should be only one class in the list.
        plugin = list_plugins("machinery")[0]
        # Initialize the machine manager.
        machinery = plugin()

        # Find its configuration file.
        conf = os.path.join(DETECTOR_ROOT, "conf", "%s.conf" % machinery_name)

        if not os.path.exists(conf):
            raise DetectorCriticalError("The configuration file for machine "
                                      "manager \"{0}\" does not exist at path:"
                                      " {1}".format(machinery_name, conf))

        # Provide a dictionary with the configuration options to the
        # machine manager instance.
        machinery.set_options(Config(machinery_name))

        # Initialize the machine manager.
        try:
            machinery.initialize(machinery_name)
        except DetectorMachineError as e:
            raise DetectorCriticalError("Error initializing machines: %s" % e)

        # At this point all the available machines should have been identified
        # and added to the list. If none were found, Detector needs to abort the
        # execution.
        if not len(machinery.machines()):
            raise DetectorCriticalError("No machines available.")
        else:
            log.info("Loaded %s machine/s", len(machinery.machines()))

        if len(machinery.machines()) > 1 and self.db.engine.name == "sqlite":
            log.warning("As you've configured Detector to execute parallel "
                        "analyses, we recommend you to switch to a MySQL or"
                        "a PostgreSQL database as SQLite might cause some "
                        "issues.")

        if len(machinery.machines()) > 4 and self.cfg.detector.process_results:
            log.warning("When running many virtual machines it is recommended "
                        "to process the results in a separate process.py to "
                        "increase throughput and stability. Please read the "
                        "documentation about the `Processing Utility`.")

        # Drop all existing packet forwarding rules for each VM. Just in case
        # Detector was terminated for some reason and various forwarding rules
        # have thus not been dropped yet.
        for machine in machinery.machines():
            if not machine.interface:
                log.info("Unable to determine the network interface for VM "
                         "with name %s, Detector will not be able to give it "
                         "full internet access or route it through a VPN! "
                         "Please define a default network interface for the "
                         "machinery or define a network interface for each "
                         "VM.", machine.name)
                continue


    def stop(self):
        """Stop scheduler."""
        self.running = False
        # Shutdown machine manager (used to kill machines that still alive).
        machinery.shutdown()

    def start(self):
        """Start scheduler."""
        self.initialize()

        log.info("Waiting for analysis tasks.")

        # Message queue with threads to transmit exceptions (used as IPC).
        errors = Queue.Queue()

        # Command-line overrides the configuration file.
        if self.maxcount is None:
            self.maxcount = self.cfg.detector.max_analysis_count

        # This loop runs forever.
        while self.running:
            time.sleep(1)

            # Wait until the machine lock is not locked. This is only the case
            # when all machines are fully running, rather that about to start
            # or still busy starting. This way we won't have race conditions
            # with finding out there are no available machines in the analysis
            # manager or having two analyses pick the same machine.
            if not machine_lock.acquire(False):
                continue

            machine_lock.release()

            # If not enough free disk space is available, then we print an
            # error message and wait another round (this check is ignored
            # when the freespace configuration variable is set to zero).
            if self.cfg.detector.freespace:
                # Resolve the full base path to the analysis folder, just in
                # case somebody decides to make a symbolic link out of it.
                dir_path = os.path.join(DETECTOR_ROOT, "storage", "analyses")

                # TODO: Windows support
                if hasattr(os, "statvfs"):
                    dir_stats = os.statvfs(dir_path)

                    # Calculate the free disk space in megabytes.
                    space_available = dir_stats.f_bavail * dir_stats.f_frsize
                    space_available /= 1024 * 1024

                    if space_available < self.cfg.detector.freespace:
                        log.error("Not enough free disk space! (Only %d MB!)",
                                  space_available)
                        continue

            # Have we limited the number of concurrently executing machines?
            if self.cfg.detector.max_machines_count:
                # Are too many running?
                if len(machinery.running()) >= self.cfg.detector.max_machines_count:
                    continue

            # If no machines are available, it's pointless to fetch for
            # pending tasks. Loop over.
            if not machinery.availables():
                continue

            # Exits if max_analysis_count is defined in the configuration
            # file and has been reached.
            if self.maxcount and self.total_analysis_count >= self.maxcount:
                if active_analysis_count <= 0:
                    log.debug("Reached max analysis count, exiting.")
                    self.stop()
                continue

            # Fetch a pending analysis task.
            # TODO This fixes only submissions by --machine, need to add
            # other attributes (tags etc).
            # TODO We should probably move the entire "acquire machine" logic
            # from the Analysis Manager to the Scheduler and then pass the
            # selected machine onto the Analysis Manager instance.
            task, available = None, False
            for machine in self.db.get_available_machines():
                task = self.db.fetch(machine=machine.name)
                if task:
                    break

                if machine.is_analysis():
                    available = True

            # We only fetch a new task if at least one of the available
            # machines is not a "service" machine (again, please refer to the
            # services auxiliary module for more information on service VMs).
            if not task and available:
                task = self.db.fetch(service=False)

            if task:
                log.debug("Processing task #%s", task.id)
                self.total_analysis_count += 1

                # Initialize and start the analysis manager.
            #    analysis = AnalysisManager(task, errors)
             #   analysis.daemon = True
             #   analysis.start()

            # Deal with errors.
            try:
                raise errors.get(block=False)
            except Queue.Empty:
                pass

        log.debug("End of analyses.")
