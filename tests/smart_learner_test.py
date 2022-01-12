import unittest
import sys
sys.path.append("./")
from ota import buildOTA, OTAToDOT
from smart_learner import learn_ota, generate_pair, compute_max_time
from equivalence import ota_equivalent
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

            "4_4_20/4_4_20-1.json",   # 5.403
            "4_4_20/4_4_20-2.json",   # 13.580
            "4_4_20/4_4_20-3.json",   # 16.203
            "4_4_20/4_4_20-4.json",   # 6.602
            "4_4_20/4_4_20-5.json",   # 4.603
            "4_4_20/4_4_20-6.json",   # 9.960
            "4_4_20/4_4_20-7.json",   # 9.367
            "4_4_20/4_4_20-8.json",   # 7.788
            "4_4_20/4_4_20-9.json",   # 6.124
            "4_4_20/4_4_20-10.json",  # 12.825

            "7_2_10/7_2_10-1.json",   # 6.978
            "7_2_10/7_2_10-2.json",   # 4.171
            "7_2_10/7_2_10-3.json",   # 10.347
            "7_2_10/7_2_10-4.json",   # 6.481
            "7_2_10/7_2_10-5.json",   # 3.218
            "7_2_10/7_2_10-6.json",   # 4.889
            "7_2_10/7_2_10-7.json",   # 5.779
            "7_2_10/7_2_10-8.json",   # 3.943
            "7_2_10/7_2_10-9.json",   # 9.611
            "7_2_10/7_2_10-10.json",  # 6.932

            "7_4_10/7_4_10-1.json",   # 9.561
            "7_4_10/7_4_10-2.json",   # 5.741
            "7_4_10/7_4_10-3.json",   # 14.570
            "7_4_10/7_4_10-4.json",   # 4.422
            "7_4_10/7_4_10-5.json",   # 13.663
            "7_4_10/7_4_10-6.json",   # 7.115
            "7_4_10/7_4_10-7.json",   # 6.618
            "7_4_10/7_4_10-8.json",   # 7.693
            "7_4_10/7_4_10-9.json",   # 9.580
            "7_4_10/7_4_10-10.json",  # 6.487

            "7_6_10/7_6_10-1.json",   # 13.068
            "7_6_10/7_6_10-2.json",   # 13.410
            "7_6_10/7_6_10-3.json",   # 12.068
            "7_6_10/7_6_10-4.json",   # 10.391
            "7_6_10/7_6_10-5.json",   # 12.066
            "7_6_10/7_6_10-6.json",   # 22.835
            "7_6_10/7_6_10-7.json",   # 12.354
            "7_6_10/7_6_10-8.json",   # 19.355
            "7_6_10/7_6_10-9.json",   # 13.374
            "7_6_10/7_6_10-10.json",  # 16.102

            "7_4_20/7_4_20-1.json",   # 31.038
            "7_4_20/7_4_20-2.json",   # 31.012
            "7_4_20/7_4_20-3.json",   # 14.370
            "7_4_20/7_4_20-4.json",   # 12.790
            "7_4_20/7_4_20-5.json",   # 10.670
            "7_4_20/7_4_20-6.json",   # 26.393
            "7_4_20/7_4_20-7.json",   # 18.958
            "7_4_20/7_4_20-8.json",   # 13.320
            "7_4_20/7_4_20-9.json",   # 21.074
            "7_4_20/7_4_20-10.json",  # 11.272

            "10_4_20/10_4_20-1.json",   # 28.586
            "10_4_20/10_4_20-2.json",   # 21.877
            "10_4_20/10_4_20-3.json",   # 19.590
            "10_4_20/10_4_20-4.json",   # 34.059
            "10_4_20/10_4_20-5.json",   # 39.308
            "10_4_20/10_4_20-6.json",   # 14.243
            "10_4_20/10_4_20-7.json",   # 24.364
            "10_4_20/10_4_20-8.json",   # 28.295
            "10_4_20/10_4_20-9.json",   # 27.977
            "10_4_20/10_4_20-10.json",  # 44.478

            "12_4_20/12_4_20-1.json",   # 26.557
            "12_4_20/12_4_20-2.json",   # 39.706
            "12_4_20/12_4_20-3.json",   # 46.397
            "12_4_20/12_4_20-4.json",   # 40.688
            "12_4_20/12_4_20-5.json",   # 41.544
            "12_4_20/12_4_20-6.json",   # 44.134
            "12_4_20/12_4_20-7.json",   # 35.235
            "12_4_20/12_4_20-8.json",   # 64.871
            "12_4_20/12_4_20-9.json",   # 25.688
            "12_4_20/12_4_20-10.json",  # 33.744

            "14_4_20/14_4_20-1.json",   # 27.486
            "14_4_20/14_4_20-2.json",   # 30.856
            "14_4_20/14_4_20-3.json",   # 41.643
            "14_4_20/14_4_20-4.json",   # 45.232
            "14_4_20/14_4_20-5.json",   # 38.071
            "14_4_20/14_4_20-6.json",   # 34.595
            "14_4_20/14_4_20-7.json",   # 43.361
            "14_4_20/14_4_20-8.json",   # 23.895
            "14_4_20/14_4_20-9.json",   # 34.870
            "14_4_20/14_4_20-10.json",  # 54.372

            "TCP.json",
        ]

        profile = False
        graph = False

        if profile:
            pr = cProfile.Profile()
            pr.enable()

        with open("output3.txt", "w") as output_file:
            for f in test_cases:
                print("file name: %s", f)
                o = buildOTA("./examples/%s" % f)
                start_time = time.time()
                learned_ota, mem_num, eq_num = learn_ota(o, limit=150, verbose=False)

                max_time = compute_max_time(o)
                res, ctx = ota_equivalent(max_time, learned_ota, o)
                assert res, ("missed ctx %s" % ctx)

                end_time = time.time()
                output_file.write("Test %s: %.3f (s) Membership query: %d Equivalence query: %d\n" 
                            % (f, end_time - start_time, mem_num, eq_num))
                output_file.flush()
                if graph:
                    OTAToDOT(o, "ota_original")
                    OTAToDOT(learned_ota, "ota_learned")

        if profile:
            p = Stats(pr)
            p.strip_dirs()
            p.sort_stats('cumtime')
            p.print_stats()

if __name__ == "__main__":
    unittest.main()
