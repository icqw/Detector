import os


from lib.detector.common.constants import DETECTOR_ROOT
from lib.detector.core.startup import check_working_directory,check_configs
from lib.detector.core.startup import create_structure

def detector_init():
    cur_path = os.getcwd()
    os.chdir(DETECTOR_ROOT)

    check_working_directory()
    check_configs()
    create_structure()

###
    init_modules()
    init_tasks()
    init_yara()
    init_binaries()
    init_rooter()
    init_routing()
def detector_main():

    return

if __name__=="__main__":
   # try:
        detector_init()


