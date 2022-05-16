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
            # "DOTA/a3.json",
            # "DOTA/a.json", # 0.194
            # "DOTA/b.json", # 0.071
            # "DOTA/c.json", # 0.190
            # "DOTA/d.json", # 0.072
            # "DOTA/e.json", # 0.086
            # "DOTA/f.json", # 0.053
            # "DOTA/empty.json", # 0.011
            # "DOTA/3_2_10/3_2_10-1.json", # 0.069
            # "DOTA/3_2_10/3_2_10-2.json", # 0.167
            # "DOTA/3_2_10/3_2_10-3.json", # 0.268
            # "DOTA/3_2_10/3_2_10-4.json", # 0.104
            # "DOTA/3_2_10/3_2_10-5.json", # 0.068
            # "DOTA/3_2_10/3_2_10-6.json", # 0.125
            # "DOTA/3_2_10/3_2_10-7.json", # 0.287
            # "DOTA/3_2_10/3_2_10-8.json", # 0.168
            # "DOTA/3_2_10/3_2_10-9.json", # 0.127
            # "DOTA/3_2_10/3_2_10-10.json", # 0.215
            # "DOTA/4_2_10/4_2_10-1.json", # 0.170
            # "DOTA/4_2_10/4_2_10-2.json", # 0.174
            # "DOTA/4_2_10/4_2_10-3.json", # 0.167
            # "DOTA/4_2_10/4_2_10-4.json", # 0.311
            # "DOTA/4_2_10/4_2_10-5.json", # 0.218
            # "DOTA/4_2_10/4_2_10-6.json", # 0.354
            # "DOTA/4_2_10/4_2_10-7.json", # 0.187
            # "DOTA/4_2_10/4_2_10-8.json", # 0.182
            # "DOTA/4_2_10/4_2_10-9.json", # 0.357
            # "DOTA/4_2_10/4_2_10-10.json", # 0.372
            # "DOTA/5_2_10/5_2_10-1.json", # 0.547
            # "DOTA/5_2_10/5_2_10-2.json", # 0.414
            # "DOTA/5_2_10/5_2_10-3.json", # 0.327
            # "DOTA/5_2_10/5_2_10-4.json", # 0.499
            # "DOTA/5_2_10/5_2_10-5.json", # 0.351
            # "DOTA/5_2_10/5_2_10-6.json", # 0.507
            # "DOTA/5_2_10/5_2_10-7.json", # 0.354
            # "DOTA/5_2_10/5_2_10-8.json", # 0.411
            # "DOTA/5_2_10/5_2_10-9.json", # 0.367
            # "DOTA/5_2_10/5_2_10-10.json", # 0.530
            # "DOTA/6_2_10/6_2_10-1.json", # 0.223
            # "DOTA/6_2_10/6_2_10-2.json", # 0.937
            # "DOTA/6_2_10/6_2_10-3.json", # 1.356
            # "DOTA/6_2_10/6_2_10-4.json", # 1.147
            # "DOTA/6_2_10/6_2_10-5.json", # 1.160
            # "DOTA/6_2_10/6_2_10-6.json", # 0.708
            # "DOTA/6_2_10/6_2_10-7.json", # 0.703
            # "DOTA/6_2_10/6_2_10-8.json", # 1.255
            # "DOTA/6_2_10/6_2_10-9.json", # 2.087
            # "DOTA/6_2_10/6_2_10-10.json", # 0.968
            # "DOTA/4_4_20/4_4_20-1.json", # 1.716
            # "DOTA/4_4_20/4_4_20-2.json", # 2.120
            # "DOTA/4_4_20/4_4_20-3.json", # 1.993
            # "DOTA/4_4_20/4_4_20-4.json", # 1.254
            # "DOTA/4_4_20/4_4_20-5.json", # 1.221
            # "DOTA/4_4_20/4_4_20-6.json", # 2.266
            # "DOTA/4_4_20/4_4_20-7.json", # 1.634
            # "DOTA/4_4_20/4_4_20-8.json", # 1.854
            # "DOTA/4_4_20/4_4_20-9.json", # 1.362
            # "DOTA/4_4_20/4_4_20-10.json", # 2.910
            # "DOTA/7_2_10/7_2_10-1.json", # 6.645
            # "DOTA/7_2_10/7_2_10-2.json", # 2.312
            # "DOTA/7_2_10/7_2_10-3.json", # 3.239
            # "DOTA/7_2_10/7_2_10-4.json", # 2.742
            # "DOTA/7_2_10/7_2_10-5.json", # 1.456
            # "DOTA/7_2_10/7_2_10-6.json", # 2.562
            # "DOTA/7_2_10/7_2_10-7.json", # 2.530
            # "DOTA/7_2_10/7_2_10-8.json", # 1.082
            # "DOTA/7_2_10/7_2_10-9.json", # 2.757
            # "DOTA/7_2_10/7_2_10-10.json", # 4.381
            # "DOTA/7_4_10/7_4_10-1.json", # 3.116
            # "DOTA/7_4_10/7_4_10-2.json", # 2.132
            # "DOTA/7_4_10/7_4_10-3.json", # 3.851
            # "DOTA/7_4_10/7_4_10-4.json", # 1.622
            # "DOTA/7_4_10/7_4_10-5.json", # 4.210
            # "DOTA/7_4_10/7_4_10-6.json", # 3.080
            # "DOTA/7_4_10/7_4_10-7.json", # 3.081
            # "DOTA/7_4_10/7_4_10-8.json", # 3.068
            # "DOTA/7_4_10/7_4_10-9.json", # 3.366
            # "DOTA/7_4_10/7_4_10-10.json", # 1.842
            # "DOTA/7_6_10/7_6_10-1.json", # 4.987
            # "DOTA/7_6_10/7_6_10-2.json", # 5.206
            # "DOTA/7_6_10/7_6_10-3.json", # 3.530
            # "DOTA/7_6_10/7_6_10-4.json", # 2.443
            # "DOTA/7_6_10/7_6_10-5.json", # 4.556
            # "DOTA/7_6_10/7_6_10-6.json", # 3.692
            # "DOTA/7_6_10/7_6_10-7.json", # 4.787
            # "DOTA/7_6_10/7_6_10-8.json", # 7.752
            # "DOTA/7_6_10/7_6_10-9.json", # 4.668
            # "DOTA/7_6_10/7_6_10-10.json", # 4.631
            # "DOTA/7_4_20/7_4_20-1.json", # 6.485
            # "DOTA/7_4_20/7_4_20-2.json", # 3.900
            # "DOTA/7_4_20/7_4_20-3.json", # 3.206
            # "DOTA/7_4_20/7_4_20-4.json", # 3.076
            # "DOTA/7_4_20/7_4_20-5.json", # 1.998
            # "DOTA/7_4_20/7_4_20-6.json", # 4.756
            # "DOTA/7_4_20/7_4_20-7.json", # 3.428
            # "DOTA/7_4_20/7_4_20-8.json", # 2.742
            # "DOTA/7_4_20/7_4_20-9.json", # 4.694
            # "DOTA/7_4_20/7_4_20-10.json", # 2.652
            # "DOTA/10_4_20/10_4_20-1.json", # 8.937
            # "DOTA/10_4_20/10_4_20-2.json", # 8.232
            # "DOTA/10_4_20/10_4_20-3.json", # 6.366
            # "DOTA/10_4_20/10_4_20-4.json", # 10.094
            # "DOTA/10_4_20/10_4_20-5.json", # 5.797
            # "DOTA/10_4_20/10_4_20-6.json", # 4.497
            # "DOTA/10_4_20/10_4_20-7.json", # 8.745
            # "DOTA/10_4_20/10_4_20-8.json", # 6.680
            # "DOTA/10_4_20/10_4_20-9.json", # 6.846
            # "DOTA/10_4_20/10_4_20-10.json", # 8.518
            # "DOTA/12_4_20/12_4_20-1.json", # 6.817
            # "DOTA/12_4_20/12_4_20-2.json", # 12.616
            # "DOTA/12_4_20/12_4_20-3.json", # 11.732
            # "DOTA/12_4_20/12_4_20-4.json", # 17.564
            # "DOTA/12_4_20/12_4_20-5.json", # 11.579
            # "DOTA/12_4_20/12_4_20-6.json", # 11.980
            # "DOTA/12_4_20/12_4_20-7.json", # 12.651
            # "DOTA/12_4_20/12_4_20-8.json", # 14.110
            # "DOTA/12_4_20/12_4_20-9.json", # 8.514
            # "DOTA/12_4_20/12_4_20-10.json", # 8.638
            # "DOTA/14_4_20/14_4_20-1.json", # 18.507
            # "DOTA/14_4_20/14_4_20-2.json", # 15.911
            # "DOTA/14_4_20/14_4_20-3.json", # 18.936
            # "DOTA/14_4_20/14_4_20-4.json", # 14.728
            # "DOTA/14_4_20/14_4_20-5.json", # 17.541
            # "DOTA/14_4_20/14_4_20-6.json", # 14.094
            # "DOTA/14_4_20/14_4_20-7.json", # 20.458
            # "DOTA/14_4_20/14_4_20-8.json", # 10.513
            # "DOTA/14_4_20/14_4_20-9.json", # 35.382
            # "DOTA/14_4_20/14_4_20-10.json", # 16.522

            "DOTA/OTAs/Light.json",
            "DOTA/OTAs/Train.json",
            "DOTA/OTAs/AKM.json",
            "DOTA/OTAs/CAS.json",
            "DOTA/OTAs/TCP.json",
            "DOTA/OTAs/PC.json"
        ]

        profile = False
        graph = False

        if profile:
            pr = cProfile.Profile()
            pr.enable()

        with open("output.txt", "w") as output_file:
            locs = 0
            mems, eqs, timer = [], [], []
            trans_num = 0
            for f in test_cases:
                print("file name: %s", f)
                o = buildOTA("./examples/%s" % f)
                trans_num += len(o.trans)
                start_time = time.perf_counter()
                learned_ota, mem_num, eq_num = learn_ota(o, limit=150, verbose=False)
                end_time = time.perf_counter()
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
        # print(max_time)
        if profile:
            p = Stats(pr)
            p.strip_dirs()
            p.sort_stats('cumtime')
            p.print_stats()

if __name__ == "__main__":
    unittest.main()
