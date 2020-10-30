# Data structure for the learner.


class TestSequence:
    """Represents data for a single test sequence.


    """
    def __init__(self, tws):
        self.tws = tws
        self.info = dict()

    def testSuffix(self, ota, tws2, shift=0):
        """Test the given timed words starting from self.
        
        tws2 - list(TimedWord): suffix to be appended.
        shift - additional time before appending suffix.

        """
        assert len(tws2) > 0, 'testSuffix: expect nonempty suffix.'
        if shift > 0:
            tws2 = [TimedWord(tws2[0].action, tws2[0].time + shift)] + tws2[1:]
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
        self.actions = actions

        self.R = dict()  # Test sequences
        self.E = []  # Discriminator sequences

    