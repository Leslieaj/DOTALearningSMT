# Unit test for OTA

import unittest
import sys
sys.path.append("./")
from ota import buildOTA, buildAssistantOTA


class OTATest(unittest.TestCase):
    def testBuildOTA(self):
        ota = buildOTA('./examples/b.json')
        assist_ota = buildAssistantOTA(ota)
        print(ota)
        print(assist_ota)


if __name__ == "__main__":
    unittest.main()
