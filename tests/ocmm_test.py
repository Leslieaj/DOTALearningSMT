import unittest
import sys
sys.path.append("./")
from ota import TimedWord
from ocmm import IOTimedWord, buildOCMM, buildAssistantOCMM

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
            ([],[],[]),
            ([TimedWord('press?', 1)], ['void'], ['void']),
            ([TimedWord('press?', 1), TimedWord('release?',4.5)], ['void','void'], ['void','void']),
            ([TimedWord('press?', 1), TimedWord('release?',5)], ['void','void'], ['void','void']),
            ([TimedWord('press?', 1), TimedWord('void',5)], ['void','beep!'], ['void','beep!']),
        ]
        for itws, res1, res2 in test_data:
            self.assertEqual(ocmm.runInputTimedWord(itws), res1)
            self.assertEqual(ocmm.runInputTimedWord(itws), res2)

    # def testRunIOTimedWord(self):
    #     ocmm = buildOCMM('./examples/MMT/OCMMs/Light.json')
    #     # assist_ota = buildAssistantOTA(ota)
    #     test_data = [
    #         ([], 1),
    #         ([('press?','void', 1)], 1),
    #         ([('press','void', 1)], -1),
    #         ([('press?', 'beep!', 1)], -1),
    #         ([('press?', 'void', 1), ('void','beep!',5)], 1),
    #         ([('press?', 'void', 1), ('release?','void',4.55)], 1),
    #         ([('press?', 'void', 1), ('release?','void',6.55)], -1),
    #     ]
    #     for tws, res in test_data:
    #         iotws = [IOTimedWord(input, output, time) for input, output, time in tws]
    #         self.assertEqual(ocmm.runIOTimedWord(iotws), res)
    #         # self.assertEqual(assist_ota.runTimedWord(tws), res)


if __name__ == "__main__":
    unittest.main()