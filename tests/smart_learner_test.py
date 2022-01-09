import unittest

from ota import buildOTA
from smart_learner import generate_resets_pairs, learn_ota
from ota import TimedWord
from pstats import Stats
import cProfile
import time


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
            "4_2_10/4_2_10-9.json",
            "4_2_10/4_2_10-10.json",

            "5_2_10/5_2_10-1.json",
            "5_2_10/5_2_10-2.json",
            "5_2_10/5_2_10-3.json",
            "5_2_10/5_2_10-4.json",
            "5_2_10/5_2_10-5.json",
            "5_2_10/5_2_10-6.json",
            "5_2_10/5_2_10-7.json",
            "5_2_10/5_2_10-8.json",
            "5_2_10/5_2_10-9.json",
            "5_2_10/5_2_10-10.json",

            "6_2_10/6_2_10-1.json",
            "6_2_10/6_2_10-2.json",
            "6_2_10/6_2_10-3.json",
            "6_2_10/6_2_10-4.json",
            "6_2_10/6_2_10-5.json",
            "6_2_10/6_2_10-6.json",
            "6_2_10/6_2_10-7.json",
            "6_2_10/6_2_10-8.json",
            "6_2_10/6_2_10-9.json",
            "6_2_10/6_2_10-10.json",

            "4_4_20/4_4_20-1.json",   # 28.701
            "4_4_20/4_4_20-2.json",   # 38.981
            "4_4_20/4_4_20-3.json",   # 82.881
            "4_4_20/4_4_20-4.json",   # 21.643
            "4_4_20/4_4_20-5.json",   # 17.175
            "4_4_20/4_4_20-6.json",   # 51.782
            "4_4_20/4_4_20-7.json",   # 26.236
            "4_4_20/4_4_20-8.json",   # 28.742
            "4_4_20/4_4_20-9.json",   # 19.988
            "4_4_20/4_4_20-10.json",  # 81.377

            "7_2_10/7_2_10-1.json",   # 79.932
            "7_2_10/7_2_10-2.json",   # 40.449
            "7_2_10/7_2_10-3.json",   # 76.530
            "7_2_10/7_2_10-4.json",   # 58.413
            "7_2_10/7_2_10-5.json",   # 33.880
            "7_2_10/7_2_10-6.json",   # 62.084
            "7_2_10/7_2_10-7.json",   # 72.579
            "7_2_10/7_2_10-8.json",   # 16.030
            "7_2_10/7_2_10-9.json",   # 59.683
            "7_2_10/7_2_10-10.json",  # 106.153
        ]

        profile = False
        if profile:
            pr = cProfile.Profile()
            pr.enable()

        with open("output", "w") as output_file:
            for f in test_cases:
                o = buildOTA("./examples/%s" % f)
                start_time = time.time()
                _ = learn_ota(o, limit=100, verbose=False)
                end_time = time.time()
                output_file.write("Test %s: %.3f (s)\n" % (f, end_time - start_time))
                output_file.flush()

        if profile:
            p = Stats(pr)
            p.strip_dirs()
            p.sort_stats('cumtime')
            p.print_stats()

if __name__ == "__main__":
    unittest.main()