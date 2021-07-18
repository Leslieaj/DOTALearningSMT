import unittest

from smart_learner import generate_resets_pairs, generate_row_resets
from ota import TimedWord

class SmartLearnLearnerTest(unittest.TestCase):
    def testGeneratePairs(self):
        test_cases = [
            [(TimedWord('a', 0.5),), (TimedWord('a', 0.5),), 
            ((0, 0), (1, 1))],
            [(TimedWord('a', 1.5),), (TimedWord('a', 1),), 
            ((0, 0), (0, 1), (1, 0), (1, 1))],
            [(TimedWord('a', 1), TimedWord('a', 2)),(TimedWord('a', 1), TimedWord('a', 2)),
            ((0, 0), (1, 1), (2, 2))],
            [(TimedWord('a', 1), TimedWord('a', 2)), (TimedWord('a', 1), TimedWord('a', 1.5)),
            ((0, 0), (1, 1), (1, 2), (2, 1), (2, 2))],
            [(TimedWord('a', 1), TimedWord('a', 2)), (TimedWord('a', 1),),
            ((0, 0), (1, 1), (2, 1))],
            [(TimedWord('a', 1), TimedWord('a', 2)), (TimedWord('b', 1),),
            ((0, 0), (0, 1), (1, 0), (1, 1), (2, 0), (2, 1))],
        ]

        for tw1, tw2, result in test_cases:
            self.assertEqual(generate_resets_pairs(tw1, tw2), result)


    def testGenerateRowResets(self):
        test_cases = [
            [(TimedWord('a', 0.5),), (TimedWord('a', 0.5),),
            ({(TimedWord('a',0.5),): True}, {(TimedWord('a',0.5),): False})],

            [(TimedWord('a', 1.5),), (TimedWord('a', 1),),
            ({(TimedWord('a',1.5),): True, (TimedWord('a',1),): True}, 
            {(TimedWord('a',1.5),): True, (TimedWord('a',1),): False}, 
            {(TimedWord('a',1.5),): False, (TimedWord('a',1),): True}, 
            {(TimedWord('a',1.5),): False, (TimedWord('a',1),): False})], 
            
            [(TimedWord('a', 1), TimedWord('a', 2)),(TimedWord('a', 1), TimedWord('a', 2)),
            ({(TimedWord('a',1),): True, (TimedWord('a',1), TimedWord('a',2)): False}, 
            {(TimedWord('a',1),): False, (TimedWord('a',1), TimedWord('a',2)): True}, 
            {(TimedWord('a',1),): False, (TimedWord('a',1), TimedWord('a',2)): False})],
            
            [(TimedWord('a', 1), TimedWord('a', 2)), (TimedWord('a', 1), TimedWord('a', 1.5)),
            ({(TimedWord('a',1),): True, (TimedWord('a',1), TimedWord('a',2)): False, (TimedWord('a',1), TimedWord('a',1.5)): False}, 
            {(TimedWord('a',1),): False, (TimedWord('a',1), TimedWord('a',2)): True, (TimedWord('a',1), TimedWord('a',1.5)): True}, 
            {(TimedWord('a',1),): False, (TimedWord('a',1), TimedWord('a',2)): True, (TimedWord('a',1), TimedWord('a',1.5)): False}, 
            {(TimedWord('a',1),): False, (TimedWord('a',1), TimedWord('a',2)): False, (TimedWord('a',1), TimedWord('a',1.5)): True}, 
            {(TimedWord('a',1),): False, (TimedWord('a',1), TimedWord('a',2)): False, (TimedWord('a',1), TimedWord('a',1.5)): False})],
            
            [(TimedWord('a', 1), TimedWord('a', 2)), (TimedWord('a', 1),),
            ({(TimedWord('a',1),): True, (TimedWord('a',1), TimedWord('a',2)): False}, 
            {(TimedWord('a',1),): False, (TimedWord('a',1), TimedWord('a',2)): True}, 
            {(TimedWord('a',1),): False, (TimedWord('a',1), TimedWord('a',2)): False})],
            
            [(TimedWord('a', 1), TimedWord('a', 2)), (TimedWord('b', 1),),
            ({(TimedWord('a',1),): True, (TimedWord('a',1), TimedWord('a',2)): False, (TimedWord('b',1),): True}, 
            {(TimedWord('a',1),): True, (TimedWord('a',1), TimedWord('a',2)): False, (TimedWord('b',1),): False}, 
            {(TimedWord('a',1),): False, (TimedWord('a',1), TimedWord('a',2)): True, (TimedWord('b',1),): True}, 
            {(TimedWord('a',1),): False, (TimedWord('a',1), TimedWord('a',2)): True, (TimedWord('b',1),): False}, 
            {(TimedWord('a',1),): False, (TimedWord('a',1), TimedWord('a',2)): False, (TimedWord('b',1),): True}, 
            {(TimedWord('a',1),): False, (TimedWord('a',1), TimedWord('a',2)): False, (TimedWord('b',1),): False})],
        ]

        for tw1, tw2, res in test_cases:
            self.assertEqual(generate_row_resets(tw1, tw2), res)