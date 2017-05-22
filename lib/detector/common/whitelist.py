import os.path

from lib.detector.common.constants import DETECTOR_ROOT

domains = set()

def is_whitelisted_domain(domain):
    return domain in domains

# Initialize the domain whitelist.
for domain in open(os.path.join(DETECTOR_ROOT, "data", "whitelist", "domain.txt")):
    domains.add(domain.strip())
