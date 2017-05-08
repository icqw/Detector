import os

from lib.detector.common.exceptions import DetectorOperationalError



def create_folders(root=".", folders=[]):
    """Create directories.
    @param root: root path.
    @param folders: folders list to be created.
    @raise DetectorOperationalError: if fails to create folder.
    """
    for folder in folders:
        create_folder(root, folder)

def create_folder(root=".", folder=None):
    """Create directory.
    @param root: root path.
    @param folder: folder name to be created.
    @raise DetectorOperationalError: if fails to create folder.
    """
    folder_path = os.path.join(root, folder)
    if folder and not os.path.isdir(folder_path):
        try:
            os.makedirs(folder_path)
        except OSError:
            raise DetectorOperationalError("Unable to create folder: %s" %
                                         folder_path)

class Singleton(type):
    """Singleton.
    @see: http://stackoverflow.com/questions/6760685/creating-a-singleton-in-python
    """
    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(Singleton, cls).__call__(*args, **kwargs)
        return cls._instances[cls]

