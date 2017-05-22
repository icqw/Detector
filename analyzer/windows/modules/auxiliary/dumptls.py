from lib.api.process import Process
from lib.common.abstracts import Auxiliary

class DumpTLSMasterSecrets(Auxiliary):
    """Dump TLS master secrets as used by various Windows libraries."""
    def start(self):
        Process(process_name="lsass.exe").inject(track=False, mode="dumptls")
