import sys
import time
import os
import shutil

from ota import buildOTA, OTAToDOT
from smart_learner import learn_ota

if __name__ == "__main__":
    file_path = sys.argv[1]
    
    graph = False
    if len(sys.argv) == 3:
        if sys.argv[2] == "--graph=true":
            graph = True
        elif sys.argv[2] == "--graph=false":
            graph = False
        else:
            raise AssertionError("unexpected argument: %s is neither --graph=true nor --graph=false" % sys.argv[2])

    if not os.path.isfile(file_path):
        raise FileNotFoundError(file_path)
    # clear graph folder
    if graph and os.path.isdir("./dot"):
        shutil.rmtree("./dot")
    o = buildOTA(file_path)
    start_time = time.perf_counter()
    learned_ota, mem_num, eq_num = learn_ota(o, verbose=False, graph=graph)
    end_time = time.perf_counter()
    if graph:
        OTAToDOT(o, "ota_original")
        OTAToDOT(learned_ota, "ota_learned")
    print("Time: %.3f, #Membership query: %d, #Equivalence query: %d, Locations: %d" % 
            (end_time-start_time, mem_num, eq_num, len(learned_ota.locations)-1))
