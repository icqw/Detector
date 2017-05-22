import os

from lib.detector.common.abstracts import Processing
from lib.detector.common.objects import File

class DroppedBuffer(Processing):
    """Dropped buffer analysis."""

    def run(self):
        """Run analysis.
        @return: list of dropped files with related information.
        """
        self.key = "buffer"
        dropped_files = []

        for dir_name, dir_names, file_names in os.walk(self.buffer_path):
            for file_name in file_names:
                file_path = os.path.join(dir_name, file_name)
                file_info = File(file_path=file_path).get_all()
                dropped_files.append(file_info)

        return dropped_files
