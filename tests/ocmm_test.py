import profile
import unittest
import sys
sys.path.append("./")
from ota import TimedWord
from ocmm import buildOCMM, buildAssistantOCMM
import time
import ocmm_smart_learner

class OCMMTest(unittest.TestCase):
    def testBuildOCMM(self):
        ocmm = buildOCMM('./examples/MMT/OCMMs/Light.json')
        print(ocmm)

    def testBuildAssistantOCMM(self):
        ocmm = buildOCMM('./examples/MMT/OCMMs/Light.json')
        assist_ocmm = buildAssistantOCMM(ocmm)
        print(assist_ocmm)
    
    def testRunInputTimedWord(self):
        ocmm = buildOCMM('./examples/MMT/OCMMs/Light.json')
        assist_ocmm = buildAssistantOCMM(ocmm)

        test_data = [
            # (input timed word, ocmm output sequnce, assist_ocmm output sequnce)
            (tuple(),(None, 1), (None, 1)),
            ((TimedWord('press?', 1),), ('void', 1), ('void', 1)),
            ((TimedWord('press?', 1), TimedWord('release?',4.5),), ('void', 1), ('void', 1)),
            ((TimedWord('press?', 1), TimedWord('release?',5),), ('sink!', -1), ('sink!', -1)),
            ((TimedWord('press?', 1), TimedWord('void',5),), ('beep!', 1), ('beep!', 1))
        ]
        for itws, res1, res2 in test_data:
            self.assertEqual(ocmm.runTimedWord(itws), res1)
            self.assertEqual(assist_ocmm.runTimedWord(itws), res2)


if __name__ == "__main__":
    unittest.main()