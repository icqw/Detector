import os



from lib.detector.common.constants import DETECTOR_ROOT
from lib.detector.core.startup import check_working_directory,check_configs
from lib.detector.core.startup import create_structure
from lib.detector.core.resultserver import ResultServer
from lib.detector.core.scheduler import Scheduler



def detector_init():
    cur_path = os.getcwd()
    os.chdir(DETECTOR_ROOT)

    check_working_directory()
    check_configs()
    create_structure()              #create analysis dir

    #  init_modules()
    #  init_tasks()
    #  init_yara()
    #  init_binaries()
    #  init_rooter()
    # init_routing()
    ResultServer()

    os.chdir(cur_path)
###

def detector_main(max_analysis_count=0):
    """Detector main loop.
    @param max_analysis_count: kill detector after this number of analyses
    """
    cur_path = os.getcwd()
    os.chdir(DETECTOR_ROOT)

    try:
        sched = Scheduler(max_analysis_count)
        sched.start()
    except KeyboardInterrupt:
        sched.stop()

    os.chdir(cur_path)

def detector_main():

    return

if __name__=="__main__":
   # try:
        detector_init()


