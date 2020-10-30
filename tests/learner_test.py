# Unit test for learner.py

import unittest

from learner import TestSequence
from ota import TimedWord, buildOTA, buildAssistantOTA


class LearnerTest(unittest.TestCase):
    def testAllTimeVals(self):
        ts = TestSequence((TimedWord('a', 2), TimedWord('b', 0), TimedWord('b', 1)))
        self.assertEqual(ts.allTimeVals(), {0, 1, 3})

    def testGetTimeVals(self):
        ts = TestSequence((TimedWord('a', 2), TimedWord('b', 1), TimedWord('b', 1)))
        reset1 = {(TimedWord('a', 2), ): True,
                  (TimedWord('a', 2), TimedWord('b', 1)): True,
                  (TimedWord('a', 2), TimedWord('b', 1), TimedWord('b', 1)): False}
        reset2 = {(TimedWord('a', 2), ): False,
                  (TimedWord('a', 2), TimedWord('b', 1)): False,
                  (TimedWord('a', 2), TimedWord('b', 1), TimedWord('b', 1)): False}
        self.assertEqual(ts.getTimeVals(reset1), 1)
        self.assertEqual(ts.getTimeVals(reset2), 4)


if __name__ == "__main__":
    unittest.main()
