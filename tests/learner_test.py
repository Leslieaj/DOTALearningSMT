# Unit test for learner.py

import unittest

from learner import TestSequence, Learner, learn_ota
from ota import TimedWord, buildOTA, buildAssistantOTA


class LearnerTest(unittest.TestCase):
    def testAllTimeVals(self):
        ts = TestSequence((TimedWord('a', 2), TimedWord('b', 0), TimedWord('b', 1)), 1)
        self.assertEqual(ts.allTimeVals(), {0, 1, 3})

    def testGetTimeVal(self):
        ts = TestSequence((TimedWord('a', 2), TimedWord('b', 1), TimedWord('b', 1)), 1)
        reset1 = {(TimedWord('a', 2), ): True,
                  (TimedWord('a', 2), TimedWord('b', 1)): True,
                  (TimedWord('a', 2), TimedWord('b', 1), TimedWord('b', 1)): False}
        reset2 = {(TimedWord('a', 2), ): False,
                  (TimedWord('a', 2), TimedWord('b', 1)): False,
                  (TimedWord('a', 2), TimedWord('b', 1), TimedWord('b', 1)): False}
        self.assertEqual(ts.getTimeVal(reset1), 1)
        self.assertEqual(ts.getTimeVal(reset2), 4)

    def testLearner(self):
        ota = buildOTA('./examples/a.json')
        learner = Learner(ota)
        S_list = [
            (),
            (TimedWord('a', 1),),
            (TimedWord('a', 1), TimedWord('b', 1)),
        ]
        R_list = [
            (TimedWord('a', 1), TimedWord('b', 1), TimedWord('a', 1)),
        ]
        for S in S_list:
            learner.S[S] = TestSequence(S, 1)
        for R in R_list:
            learner.R[R] = TestSequence(R, 1)
        learner.E = [(TimedWord('a', 0),), (TimedWord('b', 0),),
                     (TimedWord('a', 1),), (TimedWord('b', 1),),
                     (TimedWord('a', 2),), (TimedWord('b', 2),)]

        resets, foundR = learner.findReset()
        # print(resets)
        # print(foundR)
        candidateOTA = learner.buildCandidateOTA()
        # print(candidateOTA)

    def testLearn(self):
        ota = buildOTA('./examples/e.json')
        learn_ota(ota, limit=15, verbose=False)


if __name__ == "__main__":
    unittest.main()
