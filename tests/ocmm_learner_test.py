import unittest
import cProfile
import time
import ocmm
import ocmm_smart_learner
from pstats import Stats

class OCMMLearner(unittest.TestCase):
    def testOCMMLearner(self):
        test_cases = [
            "Light", # 0.457
            "Train", # 0.996
            # "AKM", # Timeout
            # "CAS", # Timeout
            # "TCP", # Timeout
            # "PC", # Timeout
        ]

        profile = False

        if profile:
            pr = cProfile.Profile()
            pr.enable()

        for f in test_cases:
            print("file name %s" % f)
            o = ocmm.buildOCMM("./examples/MMT/OCMMs/%s.json" % f)
            start_time = time.time()
            _ = ocmm_smart_learner.learn_ota(o, limit=150, verbose=False)
            end_time = time.time()
            print("Test %s: %.3f" % (f, end_time-start_time))

        if profile:
            p = Stats(pr)
            p.strip_dirs()
            p.sort_stats('cumtime')
            p.print_stats()