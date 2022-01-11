import unittest
import sys
sys.path.append("./")
sys.path.append("..")
from ocmm import IOTimedWord, buildOCMM

class OCMMTest(unittest.TestCase):
    def testBuildOCMM(self):
        ocmm = buildOCMM('../examples/MMT/OCMMs/Light.json')
        # assist_ota = buildOCMM(ocmm)
        print(ocmm)
        # print(assist_ota)

    def testRunIOTimedWord(self):
        ocmm = buildOCMM('../examples/MMT/OCMMs/Light.json')
        # assist_ota = buildAssistantOTA(ota)
        test_data = [
            ([], 1),
            ([('press?','void', 1)], 1),
            ([('press','void', 1)], -1),
            ([('press?', 'beep!', 1)], -1),
            ([('press?', 'void', 1), ('void','beep!',5)], 1),
            ([('press?', 'void', 1), ('release?','void',4.55)], 1),
            ([('press?', 'void', 1), ('release?','void',6.55)], -1),
        ]
        for tws, res in test_data:
            iotws = [IOTimedWord(input, output, time) for input, output, time in tws]
            self.assertEqual(ocmm.runIOTimedWord(iotws), res)
            # self.assertEqual(assist_ota.runTimedWord(tws), res)


if __name__ == "__main__":
    unittest.main()