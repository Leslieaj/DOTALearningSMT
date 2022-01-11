import unittest

from ota import buildOTA
from smart_learner import generate_resets_pairs, learn_ota, generate_pair
from ota import TimedWord
from pstats import Stats
import cProfile
import time


class SmartLearnerTest(unittest.TestCase):
    def testGen(self):
        test_cases = [
            [(), (0,), ((-1, 0), (-1, -1))],
            [(0,), (0,), ((-1, -1), (0, 0))],
            [(0,), (1,), ((-1, -1), (-1, 0), (0, -1), (0, 0))],
            [(0,), (0, 1), ((-1, -1), (-1, 1), (0, 0), (0, 1))],
            [(0, 1), (0, 1), ((-1, -1), (0, 0), (1, 1))],
            [(0,), (0, 1, 2), ((-1, -1), (-1, 1), (-1, 2), (0, 0), (0, 1), (0, 2))]
        ]

        for t1, t2, pairs in test_cases:
            res = generate_pair(t1, t2)
            self.assertEqual(len(res), len(pairs))
            self.assertEqual(set(res), set(pairs))

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

            "4_4_20/4_4_20-1.json",   # 15.248
            "4_4_20/4_4_20-2.json",   # 28.131
            "4_4_20/4_4_20-3.json",   # 61.466
            "4_4_20/4_4_20-4.json",   # 12.912
            "4_4_20/4_4_20-5.json",   # 11.782
            "4_4_20/4_4_20-6.json",   # 25.469
            "4_4_20/4_4_20-7.json",   # 21.424
            "4_4_20/4_4_20-8.json",   # 15.166
            "4_4_20/4_4_20-9.json",   # 12.282
            "4_4_20/4_4_20-10.json",  # 53.159

            "7_2_10/7_2_10-1.json",   # 28.557
            "7_2_10/7_2_10-2.json",   # 8.345
            "7_2_10/7_2_10-3.json",   # 23.574
            "7_2_10/7_2_10-4.json",   # 12.515
            "7_2_10/7_2_10-5.json",   # 7.582
            "7_2_10/7_2_10-6.json",   # 12.538
            "7_2_10/7_2_10-7.json",   # 15.951
            "7_2_10/7_2_10-8.json",   # 5.860
            "7_2_10/7_2_10-9.json",   # 15.299
            "7_2_10/7_2_10-10.json",  # 34.790

            "7_4_10/7_4_10-1.json",   # 21.683
            "7_4_10/7_4_10-2.json",   # 12.678
            "7_4_10/7_4_10-3.json",   # 25.765
            "7_4_10/7_4_10-4.json",   # 9.192
            "7_4_10/7_4_10-5.json",   # 34.018
            "7_4_10/7_4_10-6.json",   # 18.949
            "7_4_10/7_4_10-7.json",   # 19.635
            "7_4_10/7_4_10-8.json",   # 20.126
            "7_4_10/7_4_10-9.json",   # 21.577
            "7_4_10/7_4_10-10.json",  # 16.221

            "7_6_10/7_6_10-1.json",   # 26.171
            "7_6_10/7_6_10-2.json",   # 38.006
            "7_6_10/7_6_10-3.json",   # 31.289
            "7_6_10/7_6_10-4.json",   # 24.207
            "7_6_10/7_6_10-5.json",   # 31.174
            "7_6_10/7_6_10-6.json",   # 38.954
            "7_6_10/7_6_10-7.json",   # 31.332
            "7_6_10/7_6_10-8.json",   # 44.004
            "7_6_10/7_6_10-9.json",   # 35.700
            "7_6_10/7_6_10-10.json",  # 39.046

            "7_4_20/7_4_20-1.json",   # 96.792
            "7_4_20/7_4_20-2.json",
            "7_4_20/7_4_20-3.json",
            "7_4_20/7_4_20-4.json",
            "7_4_20/7_4_20-5.json",
            "7_4_20/7_4_20-6.json",
            "7_4_20/7_4_20-7.json",
            "7_4_20/7_4_20-8.json",
            "7_4_20/7_4_20-9.json",
            "7_4_20/7_4_20-10.json",
        ]

        profile = False
        if profile:
            pr = cProfile.Profile()
            pr.enable()

        with open("output", "w") as output_file:
            for f in test_cases:
                print("file name: %s", f)
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