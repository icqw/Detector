import os
import codecs

from lib.detector.common.abstracts import Processing
from lib.detector.common.exceptions import DetectorProcessingError
from lib.detector.core.database import Database

class Debug(Processing):
    """Analysis debug information."""

    def run(self):
        """Run debug analysis.
        @return: debug information dict.
        """
        self.key = "debug"
        debug = {"log": "", "errors": []}

        if os.path.exists(self.log_path):
            try:
                debug["log"] = codecs.open(self.log_path, "rb", "utf-8").readlines()
            except ValueError as e:
                raise DetectorProcessingError("Error decoding %s: %s" %
                                            (self.log_path, e))
            except (IOError, OSError) as e:
                raise DetectorProcessingError("Error opening %s: %s" %
                                            (self.log_path, e))

        for error in Database().view_errors(int(self.task["id"])):
            debug["errors"].append(error.message)

        if os.path.exists(self.mitmerr_path):
            mitmerr = open(self.mitmerr_path, "rb").read()
            if mitmerr:
                debug["errors"].append(mitmerr)

        return debug
