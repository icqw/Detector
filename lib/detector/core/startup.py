import os
import logging

from lib.detector.common.constants import DETECTOR_ROOT
from lib.detector.common.exceptions import *
from lib.detector.common.utils import create_folders

def check_working_directory():
    """Checks if working directories are ready.
    @raise DetectorStartupError: if directories are not properly configured.
    """
    if not os.path.exists(DETECTOR_ROOT):
        raise DetectorStartupError("You specified a non-existing root "
                                 "directory: {0}".format(DETECTOR_ROOT))

    cwd = os.path.join(os.getcwd(), "Detector.py")
    if not os.path.exists(cwd):
        raise DetectorStartupError("You are not running Detector from it's "
                                 "root directory")
def check_configs():
    """Checks if config files exist.
    @raise DetectorStartupError: if config files do not exist.
    """
    configs = [
        os.path.join(DETECTOR_ROOT, "conf", "auxiliary.conf"),
        os.path.join(DETECTOR_ROOT, "conf", "detector.conf"),
        os.path.join(DETECTOR_ROOT, "conf", "memory.conf"),
        os.path.join(DETECTOR_ROOT, "conf", "processing.conf"),
        os.path.join(DETECTOR_ROOT, "conf", "reporting.conf"),
        os.path.join(DETECTOR_ROOT, "conf", "virtualbox.conf"),
    ]

    for config in configs:
        if not os.path.exists(config):
            raise DetectorStartupError("Config file does not exist at "
                                     "path: {0}".format(config))

    return True
def create_structure():
    """Creates Detector directories."""
    folders = [
        "log",
        "storage",
        os.path.join("storage", "analyses"),
        os.path.join("storage", "binaries"),
        os.path.join("storage", "baseline"),
    ]

    try:
        create_folders(root=DETECTOR_ROOT, folders=folders)
    except DetectorOperationalError as e:
        raise DetectorStartupError(e)

log = logging.getLogger()

def init_modules(machinery=True):
    """Initializes plugins."""
    log.debug("Importing modules...")

    # Import all auxiliary modules.
    import modules.auxiliary
    import_package(modules.auxiliary)

    # Import all processing modules.
    import modules.processing
    import_package(modules.processing)

    # Import all signatures.
    import modules.signatures
    import_package(modules.signatures)

    delete_file("modules", "reporting", "maec40.pyc")
    delete_file("modules", "reporting", "maec41.pyc")
    delete_file("modules", "reporting", "mmdef.pyc")

    # Import all reporting modules.
    import modules.reporting
    import_package(modules.reporting)

    # Import machine manager.
    if machinery:
        import_plugin("modules.machinery." + Config().cuckoo.machinery)

    for category, entries in list_plugins().items():
        log.debug("Imported \"%s\" modules:", category)

        for entry in entries:
            if entry == entries[-1]:
                log.debug("\t `-- %s", entry.__name__)
            else:
                log.debug("\t |-- %s", entry.__name__)