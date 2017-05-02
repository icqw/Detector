
import os

_current_dir = os.path.abspath(os.path.dirname(__file__))
DETECTOR_ROOT = os.path.normpath(os.path.join(_current_dir, "..", "..", ".."))

DETECTOR_VERSION = "1.0-dev"
DETECTOR_GUEST_PORT = 8000
DETECTOR_GUEST_INIT = 0x001
DETECTOR_GUEST_RUNNING = 0x002
DETECTOR_GUEST_COMPLETED = 0x003
DETECTOR_GUEST_FAILED = 0x004