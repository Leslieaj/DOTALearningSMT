import sys,time
from ota import buildOTA, OTAToDOT
from smart_learner import learn_ota
from pstats import Stats
import cProfile

def smt_learn_dota():
    profile = False
    if profile:
        pr = cProfile.Profile()
        pr.enable()
    
    paras = sys.argv
    f = str(paras[1])
    print("File %s" % f)
    o = buildOTA("./examples/%s" % f)
    start_time = time.time()
    learnt_ota = learn_ota(o, limit=100, verbose=False)
    end_time = time.time()
    print("Total time of learning: %s ." % str(end_time - start_time))

    # OTAToDOT(o, o.name)
    # OTAToDOT(learnt_ota, learnt_ota.name+"result")

    if profile:
        p = Stats(pr)
        p.strip_dirs()
        p.sort_stats('cumtime')
        p.print_stats()

if __name__ == "__main__":
    smt_learn_dota()
