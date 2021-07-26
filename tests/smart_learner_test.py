import unittest

from ota import buildOTA
from smart_learner import generate_resets_pairs, learn_ota
from ota import TimedWord
from pstats import Stats
import cProfile


class SmartLearnLearnerTest(unittest.TestCase):
    def testGeneratePairs(self):
        test_cases = [
            [(TimedWord('a', 0.5),), (TimedWord('a', 0.5),), 
            ((0, 0), (0, 1), (1, 0), (1, 1))],
            [(TimedWord('a', 1.5),), (TimedWord('a', 1),), 
            ((0, 0), (0, 1), (1, 0), (1, 1))],
            [(TimedWord('a', 1), TimedWord('a', 2)),(TimedWord('a', 1), TimedWord('a', 2)),
            ((0, 0), (0, 1), (0, 2), (1, 0), (1, 1), (1, 2), (2, 0), (2, 1), (2, 2))],
            [(TimedWord('a', 1), TimedWord('a', 2)), (TimedWord('a', 1), TimedWord('a', 1.5)),
            ((0, 0), (0, 1), (0, 2), (1, 0), (1, 1), (1, 2), (2, 0), (2, 1), (2, 2))],
            [(TimedWord('a', 1), TimedWord('a', 2)), (TimedWord('a', 1),),
            ((0, 0), (0, 1), (1, 0), (1, 1), (2, 0), (2, 1))],
            [(TimedWord('a', 1), TimedWord('a', 2)), (TimedWord('b', 1),),
            ((0, 0), (0, 1), (1, 0), (1, 1), (2, 0), (2, 1))],
        ]

        for tw1, tw2, result in test_cases:
            self.assertEqual(generate_resets_pairs(tw1, tw2), result)

    def testLearnOTA(self):
        test_cases = [
            "a.json",
            "b.json",
            "c.json",
            "d.json",
            "e.json",
            "f.json",
            "empty.json",
            "3_2_10/3_2_10-1.json",
            "3_2_10/3_2_10-2.json",
            "3_2_10/3_2_10-3.json",
            "3_2_10/3_2_10-4.json",
            "3_2_10/3_2_10-5.json",
            "3_2_10/3_2_10-6.json",
            "3_2_10/3_2_10-7.json",
            "3_2_10/3_2_10-8.json",
            "3_2_10/3_2_10-9.json",
            "3_2_10/3_2_10-10.json",
            "4_2_10/4_2_10-1.json",
            "4_2_10/4_2_10-2.json",
            "4_2_10/4_2_10-3.json",
            "4_2_10/4_2_10-4.json",
            "4_2_10/4_2_10-5.json",
            "4_2_10/4_2_10-6.json",
            "4_2_10/4_2_10-7.json",
            "4_2_10/4_2_10-8.json",
            # "4_2_10/4_2_10-9.json", # Too much steps
            "4_2_10/4_2_10-10.json",
            "5_2_10/5_2_10-1.json",
            "5_2_10/5_2_10-2.json",
            "5_2_10/5_2_10-3.json",
            "5_2_10/5_2_10-4.json",
            "5_2_10/5_2_10-5.json",
            "5_2_10/5_2_10-6.json",
            "5_2_10/5_2_10-7.json",
            "5_2_10/5_2_10-8.json",
            # "5_2_10/5_2_10-9.json", # Too much steps
            # "5_2_10/5_2_10-10.json", # Too much steps
            "6_2_10/6_2_10-1.json",
            "6_2_10/6_2_10-2.json",
            # "6_2_10/6_2_10-3.json", # Too much steps
            "6_2_10/6_2_10-4.json",
            "6_2_10/6_2_10-5.json",
            "6_2_10/6_2_10-6.json",
            "6_2_10/6_2_10-7.json",
            "6_2_10/6_2_10-8.json",
            # "6_2_10/6_2_10-9.json", # Too much steps
            # "6_2_10/6_2_10-10.json", # Too much steps
        ]

        profile = False
        if profile:
            pr = cProfile.Profile()
            pr.enable()

        for f in test_cases:
            print("File %s" % f)
            o = buildOTA("./examples/%s" % f)
            learn_ota(o, limit=100, verbose=False)

        if profile:
            p = Stats(pr)
            p.strip_dirs()
            p.sort_stats('cumtime')
            p.print_stats()

if __name__ == "__main__":
    unittest.main()