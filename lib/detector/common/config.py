import os
import ConfigParser

from lib.detector.common.constants import DETECTOR_ROOT
from lib.detector.common.exceptions import DetectorOperationalError
from lib.detector.common.objects import Dictionary


class Config:
    """Configuration file parser."""

    def __init__(self, file_name="detector", cfg=None):
        """
        @param file_name: file name without extension.
        @param cfg: configuration file path.
        """
        config = ConfigParser.ConfigParser()

        if cfg:
            config.read(cfg)
        else:
            config.read(os.path.join(DETECTOR_ROOT, "conf", "%s.conf" % file_name))

        for section in config.sections():
            setattr(self, section, Dictionary())
            for name, raw_value in config.items(section):
                try:
                    # Ugly fix to avoid '0' and '1' to be parsed as a
                    # boolean value.
                    # We raise an exception to goto fail^w parse it
                    # as integer.
                    if config.get(section, name) in ["0", "1"]:
                        raise ValueError

                    value = config.getboolean(section, name)
                except ValueError:
                    try:
                        value = config.getint(section, name)
                    except ValueError:
                        value = config.get(section, name)

                setattr(getattr(self, section), name, value)

    def get(self, section):
        """Get option.
        @param section: section to fetch.
        @raise CuckooOperationalError: if section not found.
        @return: option value.
        """
        try:
            return getattr(self, section)
        except AttributeError as e:
            raise DetectorOperationalError("Option %s is not found in "
                                         "configuration, error: %s" %
                                         (section, e))


