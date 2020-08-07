# Unit test for equivalence.py

import unittest
import sys
sys.path.append("./")
from decimal import Decimal

from interval import Interval
from ota import buildOTA, buildAssistantOTA
from equivalence import round_div_2, Letter, Letterword, init_letterword, ota_inclusion


class EquivalenceTest(unittest.TestCase):
    def testRoundDiv2(self):
        test_data = [
            ("1", "0.5"),
            ("0.8", "0.4"),
            ("0.5", "0.3"),
            ("0.3", "0.2"),
            ("0.1", "0.05"),
            ("0.15", "0.08"),
        ]

        for s, expected in test_data:
            self.assertEqual(round_div_2(Decimal(s)), Decimal(expected))

    def testDelayOne(self):
        test_data = [
            (Letterword([{Letter('A', 's1', '[0,0]')}, {Letter('B', 'q1', '(0,1)')}], [0, '0.5']),
             Letterword([{Letter('A', 's1', '(0,1)')}, {Letter('B', 'q1', '(0,1)')}], ['0.3', '0.8'])),

            (Letterword([{Letter('A', 's1', '(0,1)')}, {Letter('B', 'q1', '(0,1)')}], ['0.3', '0.7']),
             Letterword([{Letter('B', 'q1', '[1,1]')}, {Letter('A', 's1', '(0,1)')}], [0, '0.6'])),

            (Letterword([{Letter('A', 's1', '[4,4]')}, {Letter('B', 'q1', '(2,3)')}], [0, '0.5']),
             Letterword([{Letter('A', 's1', '(4,+)')}, {Letter('B', 'q1', '(2,3)')}], ['0.3', '0.8'])),

            (Letterword([{Letter('A', 's1', '(4,+)')}, {Letter('B', 'q1', '(2,3)')}], ['0.3', '0.7']),
             Letterword([{Letter('B', 'q1', '[3,3]')}, {Letter('A', 's1', '(4,+)')}], [0, '0.6'])),

            (Letterword([{Letter('A', 's1', '[3,3]')}, {Letter('B', 'q1', '(4,+)')}], [0, '0.5']),
             Letterword([{Letter('A', 's1', '(3,4)')}, {Letter('B', 'q1', '(4,+)')}], ['0.3', '0.8'])),

            (Letterword([{Letter('A', 's1', '(3,4)')}, {Letter('B', 'q1', '(4,+)')}], ['0.3', '0.7']),
             Letterword([{Letter('B', 'q1', '(4,+)')}, {Letter('A', 's1', '(3,4)')}], [0, '0.6'])),

            (Letterword([{Letter('A', 's1', '[0,0]'), Letter('B', 'q1', '[0,0]')}], [0]),
             Letterword([{Letter('A', 's1', '(0,1)'), Letter('B', 'q1', '(0,1)')}], ['0.5'])),

            (Letterword([{Letter('A', 's1', '(0,1)'), Letter('B', 'q1', '(0,1)')}], ['0.5']),
             Letterword([{Letter('A', 's1', '[1,1]'), Letter('B', 'q1', '[1,1]')}], [0])),

            (Letterword([{Letter('A', 's1', '[4,4]'), Letter('B', 'q1', '[4,4]')}], [0]),
             Letterword([{Letter('A', 's1', '(4,+)'), Letter('B', 'q1', '(4,+)')}], ['0.5'])),

            (Letterword([{Letter('A', 's1', '(4,+)'), Letter('B', 'q1', '(4,+)')}], ['0.5']),
             Letterword([{Letter('A', 's1', '(4,+)'), Letter('B', 'q1', '(4,+)')}], [0])),

            (Letterword([{Letter('A', 's1', '(4,+)'), Letter('B', 'q1', '[2,2]')}, {Letter('A', 's2', '(1,2)')}], [0, '0.5']),
             Letterword([{Letter('A', 's1', '(4,+)'), Letter('B', 'q1', '(2,3)')}, {Letter('A', 's2', '(1,2)')}], ['0.3', '0.8'])),

            (Letterword([{Letter('A', 's1', '(4,+)'), Letter('B', 'q1', '(4,+)')}, {Letter('A', 's2', '(1,2)')}], [0, '0.5']),
             Letterword([{Letter('A', 's2', '[2,2]')}, {Letter('A', 's1', '(4,+)'), Letter('B', 'q1', '(4,+)')}], [0, '0.5'])),
        ]

        for lw, expected in test_data:
            res, _ = lw.delay_one(4)
            self.assertEqual(res, expected)

    def testDelaySeq(self):
        test_data = [
            (Letterword([{Letter('A', 's1', '[0,0]')}, {Letter('B', 'q1', '(0,1)')}], [0, '0.5']), 17),
            (Letterword([{Letter('A', 's1', '[0,0]'), Letter('B', 'q1', '[1,1]')}, {Letter('A', 's2', '(0,1)')}], [0, '0.5']), 17),
            (Letterword([{Letter('A', 's1', '[0,0]')}, {Letter('B', 'q1', '(0,1)')}, {Letter('A', 's2', '(0,1)')}], [0, '0.3', '0.7']), 25),
        ]

        for lw, expected in test_data:
            seq = lw.delay_seq(4)
            self.assertEqual(len(seq), expected)

    def testCanDominate(self):
        test_data = [
            (Letterword([{Letter('A', 's1', '[0,0]')}, {Letter('B', 'q1', '(0,1)')}], [0, '0.5']),
             Letterword([{Letter('A', 's1', '[0,0]')}, {Letter('B', 'q1', '(0,1)')}], [0, '0.5']),
             True),
            (Letterword([{Letter('A', 's1', '[0,0]')}, {Letter('B', 'q1', '(0,1)')}], [0, '0.5']),
             Letterword([{Letter('A', 's1', '[0,0]')}, {Letter('B', 'q1', '(1,2)')}], [0, '0.5']),
             False),
            (Letterword([{Letter('A', 's1', '[0,0]')}, {Letter('B', 'q1', '(0,1)')}], [0, '0.5']),
             Letterword([{Letter('A', 's1', '[0,0]')}, {Letter('B', 'q1', '(0,1)'), Letter('B', 'q1', '(1,2)')}], [0, '0.5']),
             True),
            (Letterword([{Letter('A', 's1', '[0,0]')}, {Letter('B', 'q1', '(0,1)'), Letter('B', 'q1', '(1,2)')}], [0, '0.5']),
             Letterword([{Letter('A', 's1', '[0,0]')}, {Letter('B', 'q1', '(0,1)')}], [0, '0.5']),
             False),
            (Letterword([{Letter('B', 'q1', '(0,1)')}], ['0.5']),
             Letterword([{Letter('A', 's1', '[0,0]')}, {Letter('B', 'q1', '(0,1)'), Letter('B', 'q1', '(1,2)')}], [0, '0.5']),
             True),
        ]

        for lw1, lw2, expected in test_data:
            self.assertEqual(lw1.can_dominate(lw2), expected)

    def testImmediateASucc(self):
        ota_A = buildAssistantOTA(buildOTA('./examples/b.json'))
        ota_B = buildAssistantOTA(buildOTA('./examples/c.json'))
        lw = init_letterword(ota_A, ota_B)
        lw = lw.delay_seq(5)[4]
        lws = lw.immediate_asucc(ota_A, ota_B)
        lws = [lw.lst for lw in lws]
        expected = [
            [{Letter('A','3','[0,0]')}, {Letter('A','2','(2,3)'), Letter('B','2','(2,3)')}],
            [{Letter('B','4','[0,0]'), Letter('A','4','[0,0]')}],
        ]
        self.assertEqual(lws, expected)

    def testInclusion(self):
        ota_A = buildAssistantOTA(buildOTA('./examples/b.json'))
        ota_B = buildAssistantOTA(buildOTA('./examples/c.json'))
        res, ctx = ota_inclusion(5, ota_A, ota_B)
        print(res)
        if not res:
            print(ctx.find_path(ota_A, ota_B))

        ota_A = buildAssistantOTA(buildOTA('./examples/c.json'))
        ota_B = buildAssistantOTA(buildOTA('./examples/b.json'))
        res, ctx = ota_inclusion(5, ota_A, ota_B)
        print(res)
        if not res:
            print(ctx.find_path(ota_A, ota_B))


if __name__ == "__main__":
    unittest.main()
