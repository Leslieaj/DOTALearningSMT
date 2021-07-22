import unittest

from ota import buildOTA
from smart_learner import generate_resets_pairs, learn_ota
from ota import TimedWord

class SmartLearnLearnerTest(unittest.TestCase):
    def testGeneratePairs(self):
        test_cases = [
            [(TimedWord('a', 0.5),), (TimedWord('a', 0.5),), 
            ((0, 0), (0, 1), (1, 0), (1, 1))],
            [(TimedWord('a', 1.5),), (TimedWord('a', 1),), 
            ((0, 0), (0, 1), (1, 0), (1, 1))],
            [(TimedWord('a', 1), TimedWord('a', 2)),(TimedWord('a', 1), TimedWord('a', 2)),
            ((0, 0), (0, 1), (0, 2), (1, 0), (1, 1), (1, 2), (2, 0), (2, 1), (2, 2))],
            [(TimedWord('a', 1), TimedWord('a', 2)), (TimedWord('a', 1), TimedWord('a', 1.5)),
            ((0, 0), (0, 1), (0, 2), (1, 0), (1, 1), (1, 2), (2, 0), (2, 1), (2, 2))],
            [(TimedWord('a', 1), TimedWord('a', 2)), (TimedWord('a', 1),),
            ((0, 0), (0, 1), (1, 0), (1, 1), (2, 0), (2, 1))],
            [(TimedWord('a', 1), TimedWord('a', 2)), (TimedWord('b', 1),),
            ((0, 0), (0, 1), (1, 0), (1, 1), (2, 0), (2, 1))],
        ]

        for tw1, tw2, result in test_cases:
            self.assertEqual(generate_resets_pairs(tw1, tw2), result)

    def testLearnOTA(self):
        test_cases = [
            "a", "b", "c", "d", "e", "f", "empty"
        ]

        for f in test_cases:
            o = buildOTA("./examples/%s.json" % f)
            learn_ota(o, limit=30, verbose=False)


if __name__ == "__main__":
    unittest.main()