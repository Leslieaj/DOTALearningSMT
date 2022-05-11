import unittest
import sys
sys.path.append("./")
from ota import buildOTA, OTAToDOT
from smart_learner import learn_ota, generate_pair, compute_max_time
from equivalence import ota_equivalent
from pstats import Stats
import cProfile
import time
from statistics import mean


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
            # "a.json", # 0.194
            "a2.json",
            # "b.json", # 0.071
            # "c.json", # 0.190
            # "d.json", # 0.072
            # "e.json", # 0.086
            # "f.json", # 0.053
            'g.json',
            # "empty.json", # 0.011
            # "3_2_10/3_2_10-1.json", # 0.069
            # "3_2_10/3_2_10-2.json", # 0.167
            # "3_2_10/3_2_10-3.json", # 0.268
            # "3_2_10/3_2_10-4.json", # 0.104
            # "3_2_10/3_2_10-5.json", # 0.068
            # "3_2_10/3_2_10-6.json", # 0.125
            # "3_2_10/3_2_10-7.json", # 0.287
            # "3_2_10/3_2_10-8.json", # 0.168
            # "3_2_10/3_2_10-9.json", # 0.127
            # "3_2_10/3_2_10-10.json", # 0.215
            # "4_2_10/4_2_10-1.json", # 0.170
            # "4_2_10/4_2_10-2.json", # 0.174
            # "4_2_10/4_2_10-3.json", # 0.167
            # "4_2_10/4_2_10-4.json", # 0.311
            # "4_2_10/4_2_10-5.json", # 0.218
            # "4_2_10/4_2_10-6.json", # 0.354
            # "4_2_10/4_2_10-7.json", # 0.187
            # "4_2_10/4_2_10-8.json", # 0.182
            # "4_2_10/4_2_10-9.json", # 0.357
            # "4_2_10/4_2_10-10.json", # 0.372
            # "5_2_10/5_2_10-1.json", # 0.547
            # "5_2_10/5_2_10-2.json", # 0.414
            # "5_2_10/5_2_10-3.json", # 0.327
            # "5_2_10/5_2_10-4.json", # 0.499
            # "5_2_10/5_2_10-5.json", # 0.351
            # "5_2_10/5_2_10-6.json", # 0.507
            # "5_2_10/5_2_10-7.json", # 0.354
            # "5_2_10/5_2_10-8.json", # 0.411
            # "5_2_10/5_2_10-9.json", # 0.367
            # "5_2_10/5_2_10-10.json", # 0.530
            # "6_2_10/6_2_10-1.json", # 0.223
            # "6_2_10/6_2_10-2.json", # 0.937
            # "6_2_10/6_2_10-3.json", # 1.356
            # "6_2_10/6_2_10-4.json", # 1.147
            # "6_2_10/6_2_10-5.json", # 1.160
            # "6_2_10/6_2_10-6.json", # 0.708
            # "6_2_10/6_2_10-7.json", # 0.703
            # "6_2_10/6_2_10-8.json", # 1.255
            # "6_2_10/6_2_10-9.json", # 2.087
            # "6_2_10/6_2_10-10.json", # 0.968
            # "4_4_20/4_4_20-1.json", # 1.716
            # "4_4_20/4_4_20-2.json", # 2.120
            # "4_4_20/4_4_20-3.json", # 1.993
            # "4_4_20/4_4_20-4.json", # 1.254
            # "4_4_20/4_4_20-5.json", # 1.221
            # "4_4_20/4_4_20-6.json", # 2.266
            # "4_4_20/4_4_20-7.json", # 1.634
            # "4_4_20/4_4_20-8.json", # 1.854
            # "4_4_20/4_4_20-9.json", # 1.362
            # "4_4_20/4_4_20-10.json", # 2.910
            # "7_2_10/7_2_10-1.json", # 6.645
            # "7_2_10/7_2_10-2.json", # 2.312
            # "7_2_10/7_2_10-3.json", # 3.239
            # "7_2_10/7_2_10-4.json", # 2.742
            # "7_2_10/7_2_10-5.json", # 1.456
            # "7_2_10/7_2_10-6.json", # 2.562
            # "7_2_10/7_2_10-7.json", # 2.530
            # "7_2_10/7_2_10-8.json", # 1.082
            # "7_2_10/7_2_10-9.json", # 2.757
            # "7_2_10/7_2_10-10.json", # 4.381
            # "7_4_10/7_4_10-1.json", # 3.116
            # "7_4_10/7_4_10-2.json", # 2.132
            # "7_4_10/7_4_10-3.json", # 3.851
            # "7_4_10/7_4_10-4.json", # 1.622
            # "7_4_10/7_4_10-5.json", # 4.210
            # "7_4_10/7_4_10-6.json", # 3.080
            # "7_4_10/7_4_10-7.json", # 3.081
            # "7_4_10/7_4_10-8.json", # 3.068
            # "7_4_10/7_4_10-9.json", # 3.366
            # "7_4_10/7_4_10-10.json", # 1.842
            # "7_6_10/7_6_10-1.json", # 4.987
            # "7_6_10/7_6_10-2.json", # 5.206
            # "7_6_10/7_6_10-3.json", # 3.530
            # "7_6_10/7_6_10-4.json", # 2.443
            # "7_6_10/7_6_10-5.json", # 4.556
            # "7_6_10/7_6_10-6.json", # 3.692
            # "7_6_10/7_6_10-7.json", # 4.787
            # "7_6_10/7_6_10-8.json", # 7.752
            # "7_6_10/7_6_10-9.json", # 4.668
            # "7_6_10/7_6_10-10.json", # 4.631
            # "7_4_20/7_4_20-1.json", # 6.485
            # "7_4_20/7_4_20-2.json", # 3.900
            # "7_4_20/7_4_20-3.json", # 3.206
            # "7_4_20/7_4_20-4.json", # 3.076
            # "7_4_20/7_4_20-5.json", # 1.998
            # "7_4_20/7_4_20-6.json", # 4.756
            # "7_4_20/7_4_20-7.json", # 3.428
            # "7_4_20/7_4_20-8.json", # 2.742
            # "7_4_20/7_4_20-9.json", # 4.694
            # "7_4_20/7_4_20-10.json", # 2.652
            "10_4_20/10_4_20-1.json", # 8.937
            "10_4_20/10_4_20-2.json", # 8.232
            "10_4_20/10_4_20-3.json", # 6.366
            "10_4_20/10_4_20-4.json", # 10.094
            "10_4_20/10_4_20-5.json", # 5.797
            "10_4_20/10_4_20-6.json", # 4.497
            "10_4_20/10_4_20-7.json", # 8.745
            "10_4_20/10_4_20-8.json", # 6.680
            "10_4_20/10_4_20-9.json", # 6.846
            "10_4_20/10_4_20-10.json", # 8.518
            "12_4_20/12_4_20-1.json", # 6.817
            "12_4_20/12_4_20-2.json", # 12.616
            "12_4_20/12_4_20-3.json", # 11.732
            "12_4_20/12_4_20-4.json", # 17.564
            "12_4_20/12_4_20-5.json", # 11.579
            "12_4_20/12_4_20-6.json", # 11.980
            "12_4_20/12_4_20-7.json", # 12.651
            "12_4_20/12_4_20-8.json", # 14.110
            "12_4_20/12_4_20-9.json", # 8.514
            "12_4_20/12_4_20-10.json", # 8.638
            "14_4_20/14_4_20-1.json", # 18.507
            "14_4_20/14_4_20-2.json", # 15.911
            "14_4_20/14_4_20-3.json", # 18.936
            "14_4_20/14_4_20-4.json", # 14.728
            "14_4_20/14_4_20-5.json", # 17.541
            "14_4_20/14_4_20-6.json", # 14.094
            "14_4_20/14_4_20-7.json", # 20.458
            "14_4_20/14_4_20-8.json", # 10.513
            "14_4_20/14_4_20-9.json", # 35.382
            "14_4_20/14_4_20-10.json", # 16.522
# 
            # "MMT/OTAs/PC.json", # 10.470
        ]

        profile = False
        graph = False

        if profile:
            pr = cProfile.Profile()
            pr.enable()

        with open("output4.txt", "w") as output_file:
            locs = 0
            mems, eqs, timer = [], [], []
            trans_num = 0
            for f in test_cases:
                print("file name: %s" % f)
                o = buildOTA("./examples/%s" % f)
                trans_num += len(o.trans)
                start_time = time.perf_counter()
                learned_ota, mem_num, eq_num = learn_ota(o, limit=150, verbose=False)
                end_time = time.perf_counter()
                max_time = compute_max_time(o)
                res, ctx = ota_equivalent(max_time, learned_ota, o)
                assert res, ("missed counterexample %s" % ctx)
                timer.append(end_time - start_time)
                mems.append(mem_num)
                eqs.append(eq_num)
                loc = len(learned_ota.locations) - 1
                locs += loc
                output_file.write("Test %s: %.3f (s) Membership query: %d Equivalence query: %d Locations: %d\n" 
                            % (f, end_time - start_time, mem_num, eq_num, loc))
                output_file.flush()
                if graph:
                    OTAToDOT(o, "ota_original")
                    OTAToDOT(learned_ota, "ota_learned")
            output_file.write("Avg trans: %f mem: %f eq: %f loc:%f time:%f\n" % (trans_num/10, mean(mems), mean(eqs), locs/10, mean(timer)))
            output_file.write("MIN mem: %f eq: %f\n" % (min(mems), min(eqs)))
            output_file.write("MAX mem: %f eq: %f\n" % (max(mems), max(eqs)))
            output_file.write("\multirow{2}*{12\_4\_20} & \multirow{2}*{%s} & & \\textsf{OTAL} & %s & %s & %s & & %s & %s & %s & %s & &%.2f \\\\" % 
            (trans_num, min(mems), mean(mems), max(mems), min(eqs), mean(eqs), max(eqs), locs, mean(timer)))
        print(max_time)
        if profile:
            p = Stats(pr)
            p.strip_dirs()
            p.sort_stats('cumtime')
            p.print_stats()

if __name__ == "__main__":
    unittest.main()
