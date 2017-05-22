import os
import shlex

from lib.common.abstracts import Package

class Exe(Package):
    """EXE analysis package."""

    def start(self, path):
        args = self.options.get("arguments", "")

        name, ext = os.path.splitext(path)
        if not ext:
            new_path = name + ".exe"
            os.rename(path, new_path)
            path = new_path

        return self.execute(path, args=shlex.split(args))
