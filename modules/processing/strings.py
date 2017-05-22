import os.path
import re

from lib.detector.common.abstracts import Processing
from lib.detector.common.exceptions import DetectorProcessingError

class Strings(Processing):
    """Extract strings from analyzed file."""

    def run(self):
        """Run extract of printable strings.
        @return: list of printable strings.
        """
        self.key = "strings"
        strings = []

        if self.task["category"] == "file":
            if not os.path.exists(self.file_path):
                raise DetectorProcessingError("Sample file doesn't exist: \"%s\"" % self.file_path)

            try:
                data = open(self.file_path, "r").read()
            except (IOError, OSError) as e:
                raise DetectorProcessingError("Error opening file %s" % e)
            strings = re.findall("[\x1f-\x7e]{6,}", data)
            strings += [str(ws.decode("utf-16le")) for ws in re.findall("(?:[\x1f-\x7e][\x00]){6,}", data)]

        return strings
