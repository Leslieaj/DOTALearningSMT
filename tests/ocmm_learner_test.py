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
            "AKM", # 1.855
            "CAS", # 39.933
            "TCP", # 2.634
            "PC", # 11.381
        ]

        profile = False

        if profile:
            pr = cProfile.Profile()
            pr.enable()
        with open("mm1t_output.txt", "w") as output_file:
            for f in test_cases:
                print("file name %s" % f)
                o = ocmm.buildOCMM("./examples/MMT/OCMMs/%s.json" % f)
                start_time = time.time()
                learned_ota, mem_num, eq_num = ocmm_smart_learner.learn_ota(o, limit=100, verbose=False)                
                end_time = time.time()
                output_file.write("Test %s: %.3f (s) Membership query: %d Equivalence query: %d\n" 
                            % (f, end_time - start_time, mem_num, eq_num))
                output_file.flush()

        if profile:
            p = Stats(pr)
            p.strip_dirs()
            p.sort_stats('cumtime')
            p.print_stats()

if __name__ == "__main__":
    unittest.main()