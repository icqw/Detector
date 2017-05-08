class Dictionary(dict):
    """Detector custom dict."""

    def __getattr__(self, key):
        return self.get(key, None)

    __setattr__ = dict.__setitem__
    __delattr__ = dict.__delitem__

class URL:
    """URL base object."""

    def __init__(self, url):
        """@param url: URL"""
        self.url = url


class File(object):


    def __init__(self, file_path):
        """@param file_path: file path."""
        self.file_path = file_path

        # these will be populated when first accessed
        self._file_data = None
        self._crc32 = None
        self._md5 = None
        self._sha1 = None
        self._sha256 = None
        self._sha512 = None

