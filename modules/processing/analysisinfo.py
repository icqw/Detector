import time
import logging
from datetime import datetime

from lib.detector.core.database import Database
from lib.detector.common.abstracts import Processing
from lib.detector.common.constants import DETECTOR_VERSION

log = logging.getLogger(__name__)

class AnalysisInfo(Processing):
    """General information about analysis session."""

    def run(self):
        """Run information gathering.
        @return: information dict.
        """
        self.key = "info"

        if "started_on" not in self.task:
            return dict(
                version=DETECTOR_VERSION,
                started="none",
                ended="none",
                duration=-1,
                id=int(self.task["id"]),
                category="unknown",
                custom="unknown",
                machine=None,
                package="unknown"
            )

        if self.task.get("started_on") and self.task.get("completed_on"):
            started = time.strptime(self.task["started_on"], "%Y-%m-%d %H:%M:%S")
            started = datetime.fromtimestamp(time.mktime(started))
            ended = time.strptime(self.task["completed_on"], "%Y-%m-%d %H:%M:%S")
            ended = datetime.fromtimestamp(time.mktime(ended))
            duration = (ended - started).seconds
        else:
            log.critical("Failed to get start/end time from Task.")
            started, ended, duration = None, None, -1

        db = Database()

        # Fetch sqlalchemy object.
        task = db.view_task(self.task["id"], details=True)

        if task and task.guest:
            # Get machine description.
            machine = task.guest.to_dict()
            # Remove superfluous fields.
            del machine["task_id"]
            del machine["id"]
        else:
            machine = None

        return dict(
            version=DETECTOR_VERSION,
            started=self.task["started_on"],
            ended=self.task.get("completed_on", "none"),
            duration=duration,
            id=int(self.task["id"]),
            category=self.task["category"],
            custom=self.task["custom"],
            owner=self.task["owner"],
            machine=machine,
            package=self.task["package"],
            platform=self.task["platform"],
            options=self.task["options"],
            route=self.task["route"],
        )
