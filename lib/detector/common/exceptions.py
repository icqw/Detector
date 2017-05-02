class DetectorCriticalError(Exception):
    """Detector struggle in a critical error."""

class DetectorStartupError(DetectorCriticalError):
    """Error starting up Detector."""

class DetectorDatabaseError(DetectorCriticalError):
    """Detector database error."""

class DetectorDependencyError(DetectorCriticalError):
    """Missing dependency error."""

class DetectorOperationalError(Exception):
    """Detector operation error."""

class DetectorMachineError(DetectorOperationalError):
    """Error managing analysis machine."""

class DetectorAnalysisError(DetectorOperationalError):
    """Error during analysis."""

class DetectorProcessingError(DetectorOperationalError):
    """Error in processor module."""

class DetectorReportError(DetectorOperationalError):
    """Error in reporting module."""

class DetectorGuestError(DetectorOperationalError):
    """Detector guest agent error."""

class DetectorResultError(DetectorOperationalError):
    """Detector result server error."""
