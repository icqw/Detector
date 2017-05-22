import os
import codecs
import base64

from lib.detector.common.abstracts import Report
from lib.detector.common.constants import DETECTOR_ROOT
from lib.detector.common.exceptions import DetectorReportError
from lib.detector.common.objects import File

try:
    from jinja2.environment import Environment
    from jinja2.loaders import FileSystemLoader
    HAVE_JINJA2 = True
except ImportError:
    HAVE_JINJA2 = False

class ReportHTML(Report):
    """Stores report in HTML format."""

    def run(self, results):
        """Writes report.
        @param results: Detector results dict.
        @raise DetectorReportError: if fails to write report.
        """
        if not HAVE_JINJA2:
            raise DetectorReportError(
                "Failed to generate HTML report: Jinja2 library is not "
                "installed (install `pip install jinja2`)")

        shots_path = os.path.join(self.analysis_path, "shots")
        if os.path.exists(shots_path):
            shots = []
            counter = 1
            for shot_name in os.listdir(shots_path):
                if not shot_name.endswith(".jpg"):
                    continue

                shot_path = os.path.join(shots_path, shot_name)
                if not os.path.getsize(shot_path):
                    continue

                shot = {}
                shot["id"] = os.path.splitext(File(shot_path).get_name())[0]
                shot["data"] = base64.b64encode(open(shot_path, "rb").read())
                shots.append(shot)

                counter += 1

            shots.sort(key=lambda shot: shot["id"])
            results["screenshots"] = shots
        else:
            results["screenshots"] = []

        env = Environment(autoescape=True)
        env.loader = FileSystemLoader(os.path.join(DETECTOR_ROOT,
                                                   "data", "html"))

        processed = None
        mapping = [
            ("file_read", "File", "Read"),
            ("file_written", "File", "Written"),
            ("file_deleted", "File", "Deleted"),
            ("file_opened", "File", "Opened"),
            ("file_copied", "File", "Copied"),
            ("file_moved", "File", "Moved"),
            ("connects_ip", "Network", "Connects IP"),
            ("resolves_url", "Network", "Resolves URL"),
            ("fetches_url", "Network", "Fetches URL"),
            ("connects_host", "Network", "Connects Host"),
            ("downloads_file_url", "Network", "Downloads File URL"),
            ("directory_created", "Directory", "Created"),
            ("directory_removed", "Directory", "Removed"),
            ("directory_enumerated", "Directory", "Enumerated"),
            ("regkey_opened", "Registry Key", "Opened"),
            ("regkey_deleted", "Registry Key", "Deleted"),
            ("regkey_read", "Registry Key", "Read"),
            ("regkey_written", "Registry Key", "Written"),
            ("mutex", "Mutex", "Accessed"),
        ]

        processed = {}
        for proc in results.get("behavior", {}).get("generic", []):
            for orig, cat, subcat in mapping:
                if cat not in processed:
                    processed[cat] = {}

                if subcat not in processed[cat]:
                    processed[cat][subcat] = []

                # Special handling required for file moved/copied.
                if orig == "file_moved" or orig == "file_copied":
                    for src, dst in proc.get("summary", {}).get(orig, []):
                        entry = "%s -> %s" % (src, dst)
                        processed[cat][subcat].append(entry)
                    continue

                if "summary" in proc and orig in proc["summary"]:
                    for content in proc["summary"][orig]:
                        processed[cat][subcat].append(content)

        try:
            tpl = env.get_template("report.html")
            html = tpl.render({"results": results,
                               "processed": processed,
                               "mapping": mapping})
        except Exception as e:
            raise DetectorReportError("Failed to generate HTML report: %s" % e)

        try:
            report_path = os.path.join(self.reports_path, "report.html")
            with codecs.open(report_path, "w", encoding="utf-8") as report:
                report.write(html)
        except (TypeError, IOError) as e:
            raise DetectorReportError("Failed to write HTML report: %s" % e)

        return True
