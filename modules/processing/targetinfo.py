import os.path

from lib.detector.common.abstracts import Processing
from lib.detector.common.objects import File

class TargetInfo(Processing):
    """General information about a file."""

    def run(self):
        """Run file information gathering.
        @return: information dict.
        """
        self.key = "target"
        if not self.task:
            return {"category": "unknown", "file": {"name": "unknown"}}

        target_info = {"category": self.task["category"]}

        # We have to deal with file or URL targets.
        if self.task["category"] == "file":
            target_info["file"] = {}

            # et's try to get as much information as possible, i.e., the
            # filename if the file is not available anymore.
            if os.path.exists(self.file_path):
                target_info["file"] = File(self.file_path).get_all()

            target_info["file"]["name"] = File(self.task["target"]).get_name()
        elif self.task["category"] == "url":
            target_info["url"] = self.task["target"]

        return target_info
