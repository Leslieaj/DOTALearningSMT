# Unit test for OTA

import unittest
import sys
sys.path.append("./")
from ota import TimedWord, buildOTA, buildAssistantOTA


class OTATest(unittest.TestCase):
    def testBuildOTA(self):
        ota = buildOTA('./examples/b.json')
        assist_ota = buildAssistantOTA(ota)
        # print(ota)
        # print(assist_ota)

    def testRunTimedWord(self):
        ota = buildOTA('./examples/a.json')
        assist_ota = buildAssistantOTA(ota)
        test_data = [
            ([], 0),
            ([('a', 1)], 0),
            ([('a', 1), ('b', 1)], 1),
            ([('a', 0)], -1),
        ]
        for tws, res in test_data:
            tws = [TimedWord(action, time) for action, time in tws]
            self.assertEqual(ota.runTimedWord(tws), res)
            self.assertEqual(assist_ota.runTimedWord(tws), res)


if __name__ == "__main__":
    unittest.main()
