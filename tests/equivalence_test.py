# Unit test for equivalence.py

import unittest
import sys
sys.path.append("./")
from interval import Interval
from ota import buildOTA, buildAssistantOTA
from equivalence import Letter, Letterword, init_letterword, ota_inclusion


class EquivalenceTest(unittest.TestCase):
    def testDelayOne(self):
        test_data = [
            (Letterword([{Letter('A', 's1', '[0,0]')}, {Letter('B', 'q1', '(0,1)')}]),
             Letterword([{Letter('A', 's1', '(0,1)')}, {Letter('B', 'q1', '(0,1)')}])),

            (Letterword([{Letter('A', 's1', '(0,1)')}, {Letter('B', 'q1', '(0,1)')}]),
             Letterword([{Letter('B', 'q1', '[1,1]')}, {Letter('A', 's1', '(0,1)')}])),

            (Letterword([{Letter('A', 's1', '[4,4]')}, {Letter('B', 'q1', '(2,3)')}]),
             Letterword([{Letter('A', 's1', '(4,+)')}, {Letter('B', 'q1', '(2,3)')}])),

            (Letterword([{Letter('A', 's1', '(4,+)')}, {Letter('B', 'q1', '(2,3)')}]),
             Letterword([{Letter('B', 'q1', '[3,3]')}, {Letter('A', 's1', '(4,+)')}])),

            (Letterword([{Letter('A', 's1', '[3,3]')}, {Letter('B', 'q1', '(4,+)')}]),
             Letterword([{Letter('A', 's1', '(3,4)')}, {Letter('B', 'q1', '(4,+)')}])),

            (Letterword([{Letter('A', 's1', '(3,4)')}, {Letter('B', 'q1', '(4,+)')}]),
             Letterword([{Letter('B', 'q1', '(4,+)')}, {Letter('A', 's1', '(3,4)')}])),

            (Letterword([{Letter('A', 's1', '[0,0]'), Letter('B', 'q1', '[0,0]')}]),
             Letterword([{Letter('A', 's1', '(0,1)'), Letter('B', 'q1', '(0,1)')}])),

            (Letterword([{Letter('A', 's1', '(0,1)'), Letter('B', 'q1', '(0,1)')}]),
             Letterword([{Letter('A', 's1', '[1,1]'), Letter('B', 'q1', '[1,1]')}])),

            (Letterword([{Letter('A', 's1', '[4,4]'), Letter('B', 'q1', '[4,4]')}]),
             Letterword([{Letter('A', 's1', '(4,+)'), Letter('B', 'q1', '(4,+)')}])),

            (Letterword([{Letter('A', 's1', '(4,+)'), Letter('B', 'q1', '(4,+)')}]),
             Letterword([{Letter('A', 's1', '(4,+)'), Letter('B', 'q1', '(4,+)')}])),

            (Letterword([{Letter('A', 's1', '(4,+)'), Letter('B', 'q1', '[2,2]')}, {Letter('A', 's2', '(1,2)')}]),
             Letterword([{Letter('A', 's1', '(4,+)'), Letter('B', 'q1', '(2,3)')}, {Letter('A', 's2', '(1,2)')}])),

            (Letterword([{Letter('A', 's1', '(4,+)'), Letter('B', 'q1', '(4,+)')}, {Letter('A', 's2', '(1,2)')}]),
             Letterword([{Letter('A', 's2', '[2,2]')}, {Letter('A', 's1', '(4,+)'), Letter('B', 'q1', '(4,+)')}])),
        ]

        for lw, expected in test_data:
            res = lw.delay_one(4)
            self.assertEqual(res, expected)

    def testDelaySeq(self):
        test_data = [
            (Letterword([{Letter('A', 's1', '[0,0]')}, {Letter('B', 'q1', '(0,1)')}]), 17),
            (Letterword([{Letter('A', 's1', '[0,0]'), Letter('B', 'q1', '[1,1]')}, {Letter('A', 's2', '(0,1)')}]), 17),
            (Letterword([{Letter('A', 's1', '[0,0]')}, {Letter('B', 'q1', '(0,1)')}, {Letter('A', 's2', '(0,1)')}]), 25),
        ]

        for lw, expected in test_data:
            seq = lw.delay_seq(4)
            self.assertEqual(len(seq), expected)

    def testCanDominate(self):
        test_data = [
            (Letterword([{Letter('A', 's1', '[0,0]')}, {Letter('B', 'q1', '(0,1)')}]),
             Letterword([{Letter('A', 's1', '[0,0]')}, {Letter('B', 'q1', '(0,1)')}]),
             True),
            (Letterword([{Letter('A', 's1', '[0,0]')}, {Letter('B', 'q1', '(0,1)')}]),
             Letterword([{Letter('A', 's1', '[0,0]')}, {Letter('B', 'q1', '(1,2)')}]),
             False),
            (Letterword([{Letter('A', 's1', '[0,0]')}, {Letter('B', 'q1', '(0,1)')}]),
             Letterword([{Letter('A', 's1', '[0,0]')}, {Letter('B', 'q1', '(0,1)'), Letter('B', 'q1', '(1,2)')}]),
             True),
            (Letterword([{Letter('A', 's1', '[0,0]')}, {Letter('B', 'q1', '(0,1)'), Letter('B', 'q1', '(1,2)')}]),
             Letterword([{Letter('A', 's1', '[0,0]')}, {Letter('B', 'q1', '(0,1)')}]),
             False),
            (Letterword([{Letter('B', 'q1', '(0,1)')}]),
             Letterword([{Letter('A', 's1', '[0,0]')}, {Letter('B', 'q1', '(0,1)'), Letter('B', 'q1', '(1,2)')}]),
             True),
        ]

        for lw1, lw2, expected in test_data:
            self.assertEqual(lw1.can_dominate(lw2), expected)

    # def testImmediateASucc(self):
    #     ota_A = buildAssistantOTA(buildOTA('./examples/b.json'))
    #     ota_B = buildAssistantOTA(buildOTA('./examples/c.json'))
    #     lw = init_letterword(ota_A, ota_B)
    #     lw = lw.delay_seq(5)[4]
    #     lws = lw.immediate_asucc(ota_A, ota_B)
    #     lws = [lw.lst for lw in lws]
    #     expected = [
    #         [{Letter('B','3','[0,0]'), Letter('A','3','[0,0]')}, {Letter('A','2','(2,3)')}],
    #         [{Letter('A','3','[0,0]')}, {Letter('B','2','(2,3)'), Letter('A','2','(2,3)')}],
    #         [{Letter('B','4','[0,0]'), Letter('A','4','[0,0]')}],
    #     ]
    #     self.assertEqual(lws, expected)

    def testInclusion(self):
        ota_A = buildAssistantOTA(buildOTA('./examples/b.json'))
        ota_B = buildAssistantOTA(buildOTA('./examples/c.json'))
        res, ctx = ota_inclusion(5, ota_A, ota_B)
        print(res)
        print(ctx)

        ota_A = buildAssistantOTA(buildOTA('./examples/c.json'))
        ota_B = buildAssistantOTA(buildOTA('./examples/b.json'))
        res, ctx = ota_inclusion(5, ota_A, ota_B)
        print(res)
        print(ctx)
        print(ctx.pre_lw)
        print(ctx.pre_lw.pre_lw)

if __name__ == "__main__":
    unittest.main()
