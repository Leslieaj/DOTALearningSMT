# Unit test for interval.py

import unittest

from interval import Interval


class IntervalTest(unittest.TestCase):
    def testInitInterval(self):
        test_data = [
            '[0,0]', '[0,1)', '(1,2)', '(1,2]', '[0,+)', '(1,+)', '[0,10)', '[10,11)',
        ]

        for s in test_data:
            i = Interval(s)
            self.assertEqual(str(i), s)


if __name__ == "__main__":
    unittest.main()
