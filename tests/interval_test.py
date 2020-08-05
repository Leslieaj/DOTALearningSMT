# Unit test for interval.py

import unittest
from decimal import Decimal

from interval import Interval, intervals_partition, complement_intervals


class IntervalTest(unittest.TestCase):
    def testInitInterval(self):
        test_data = [
            '[0,0]', '[0,1)', '(1,2)', '(1,2]', '[0,+)', '(1,+)', '[0,10)', '[10,11)',
        ]

        for s in test_data:
            i = Interval(s)
            self.assertEqual(str(i), s)

    def testContainsPoint(self):
        test_data = [
            ("[0,0]", 0, True),
            ("[0,1)", 0, True),
            ("[0,1)", 1, False),
            ("[0,1)", Decimal("0.5"), True),
            ("[0,+)", 5, True),
            ("[4,+)", 3, False),
        ]

        for s, t, res in test_data:
            i = Interval(s)
            self.assertEqual(i.contains_point(t), res)

    def testContainsInterval(self):
        test_data = [
            ("[0,0]", "[0,0]", True),
            ("[0,1]", "[0,1)", True),
            ("[0,1)", "[0,1]", False),
            ("[0,1)", "[0,1)", True),
            ("[0,2)", "[0,1]", True),
            ("[0,+)", "[0,5]", True),
            ("[0,5]", "[0,+)", False),
        ]

        for s1, s2, res in test_data:
            i1, i2 = Interval(s1), Interval(s2)
            self.assertEqual(i1.contains_interval(i2), res)

    def testIntervalsPartition(self):
        test_data = [
            (["[1,2]", "(3,5)", "(4,6)"],
             ["[0,1)", "[1,2]", "(2,3]", "(3,4]", "(4,5)", "[5,6)", "[6,+)"]),
            (["(1,+)", "(2,3)", "(3,4)"],
             ["[0,1]", "(1,2]", "(2,3)", "[3,3]", "(3,4)", "[4,+)"])
        ]

        for intervals, expected in test_data:
            intervals = [Interval(s) for s in intervals]
            expected = [Interval(s) for s in expected]
            res = intervals_partition(intervals)
            self.assertEqual(res, expected)

    def testComplementIntervals(self):
        test_data = [
            (["[1,2]", "(3,5)", "(4,6)"], ["[0,1)", "(2,3]", "[6,+)"]),
            (["(1,+)", "(2,3)", "(3,4)"], ["[0,1]"]),
            (["(2,3]"], ["[0,2]", "(3,+)"]),
        ]

        for intervals, expected in test_data:
            intervals = [Interval(s) for s in intervals]
            expected = [Interval(s) for s in expected]
            res = complement_intervals(intervals)
            self.assertEqual(res, expected)


if __name__ == "__main__":
    unittest.main()
