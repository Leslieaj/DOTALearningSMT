# Unit test for interval.py

import unittest
from decimal import Decimal

from interval import Interval


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


if __name__ == "__main__":
    unittest.main()
