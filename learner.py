# Data structure for the learner.

from ota import TimedWord


class TestSequence:
    """Represents data for a single test sequence.

    """
    def __init__(self, tws):
        self.tws = tuple(tws)
        self.info = dict()

    def testSuffix(self, ota, tws2, shift=0):
        """Test the given timed words starting from self.
        
        tws2 - list(TimedWord): suffix to be appended.
        shift - additional time before appending suffix.

        """
        assert len(tws2) > 0, 'testSuffix: expect nonempty suffix.'
        if shift > 0:
            tws2 = (TimedWord(tws2[0].action, tws2[0].time + shift),) + tws2[1:]
        tws = tuple(self.tws + tws2)
        if tws not in self.info:
            self.info[tws] = ota.runTimedWord(tws)

        return self.info[tws]

    def allTimeVals(self):
        """Returns the set of possible time values at the end.

        This considers all possible values of resets.

        """
        vals = {0}
        cur_time = 0
        for tw in reversed(self.tws):
            if tw.time > 0:
                cur_time += tw.time
                vals.add(cur_time)
        return vals

    def getTimeVals(self, resets):
        """Given a choice of resets, find the value of time at the end."""
        cur_time = 0
        for i, tw in reversed(list(enumerate(self.tws))):
            if resets[self.tws[:i+1]]:
                return cur_time
            else:
                cur_time += tw.time
        return cur_time


class Learner:
    """Represents the state of the learner."""
    def __init__(self, ota):
        self.ota = ota
        self.actions = ota.sigma

        self.S = dict()
        self.R = dict()  # Test sequences
        self.E = []  # Discriminator sequences

    def findReset(self):
        num_guess = len(self.S) + len(self.R) - 1
        for num in range(2 ** num_guess):
            guesses = [b for b in bin(num)[2:].zfill(num_guess)]
            resets = dict()
            for i, tw in enumerate(sorted(self.S)):
                if tw != ():
                    resets[tw] = False if guesses[i-1] == '0' else True
            for i, tw in enumerate(sorted(self.R)):
                resets[tw] = False if guesses[i+len(self.S)-1] == '0' else True
        
            # print(resets)
            # for twS, info in self.S.items():
            #     print(twS, info.getTimeVals(resets))
            # for twR, info in self.R.items():
            #     print(twR, info.getTimeVals(resets))

            foundR = dict()
            for twR, infoR in self.R.items():
                foundR[twR] = None
                time_R = infoR.getTimeVals(resets)
                for twS, infoS in self.S.items():
                    time_S = infoS.getTimeVals(resets)

                    is_same = True
                    for twE in self.E:
                        if time_R == time_S:
                            res_R = infoR.testSuffix(self.ota, twE)
                            res_S = infoS.testSuffix(self.ota, twE)
                        elif time_R < time_S:
                            shift_R = time_S - time_R
                            res_R = infoR.testSuffix(self.ota, twE, shift_R)
                            res_S = infoS.testSuffix(self.ota, twE)
                        else:  # time_R > time_S
                            shift_S = time_R - time_S
                            res_R = infoR.testSuffix(self.ota, twE)
                            res_S = infoR.testSuffix(self.ota, twE, shift_S)
                        if res_R != res_S:
                            is_same = False
                            break
                    if is_same:
                        foundR[twR] = twS
                        break

            # print(foundR)
            if all(foundR[R] is not None for R in foundR):
                return resets, foundR

