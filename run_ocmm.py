import sys
import time
import os

from ocmm import buildOCMM
from ocmm_smart_learner import learn_ocmm

if __name__ == "__main__":
    file_path = sys.argv[1]
    if not os.path.isfile(file_path):
        raise FileNotFoundError(file_path)
    o = buildOCMM(file_path)
    start_time = time.perf_counter()
    learned_ota, mem_num, eq_num = learn_ocmm(o, verbose=False)
    end_time = time.perf_counter()

    print("Time: %.3f, #Membership query: %d, #Equivalence query: %d, Locations: %d" % 
            (end_time-start_time, mem_num, eq_num, len(learned_ota.locations)-1))

    