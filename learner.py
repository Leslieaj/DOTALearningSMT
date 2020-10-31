# Data structure for the learner.

from ota import Location, TimedWord, OTA, OTATran, buildAssistantOTA
from interval import Interval
from equivalence import ota_equivalent


class TestSequence:
    """Represents data for a single test sequence.

    """
    def __init__(self, tws, res):
        self.tws = tuple(tws)

        self.is_accept = (res == 1)
        self.is_sink = (res == -1)
        self.info = dict()

    def __str__(self):
        return "Accept: %s, Sink: %s, Info: %s" % (self.is_accept, self.is_sink, self.info)

    def __repr__(self):
        return str(self)

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

        self.addPath(())

    def addPath(self, tws):
        """Add the given path tws to learner.

        Add each prefix (including all of tws) to S. Then for each action a,
        add tws + (a, 0) to R.

        """
        tws = tuple(tws)
        for i in range(len(tws)+1):
            cur_tws = tws[:i]

            # If this prefix leads to the sink, add to R instead and stop.
            cur_res = self.ota.runTimedWord(cur_tws)
            if cur_res == -1:
                if cur_tws not in self.R:
                    self.R[cur_tws] = TestSequence(cur_tws, cur_res)
                break

            if cur_tws in self.R:
                self.S[cur_tws] = self.R[cur_tws]
                del self.R[cur_tws]
            elif cur_tws not in self.S:
                cur_res = self.ota.runTimedWord(cur_tws)
                self.S[cur_tws] = TestSequence(cur_tws, cur_res)

        # Add tws + (a, 0) to R, if tws does not lead to sink
        if self.ota.runTimedWord(tws) != -1:
            for act in self.actions:
                cur_tws = tws + (TimedWord(act, 0),)
                cur_res = self.ota.runTimedWord(cur_tws)
                if cur_tws not in self.R:
                    self.R[cur_tws] = TestSequence(cur_tws, cur_res)
        
    def findReset(self):
        non_sink_R = dict((twR, infoR) for twR, infoR in self.R.items()
                          if not infoR.is_sink)
        num_guess = len(self.S) + len(non_sink_R) - 1
        for num in range(2 ** num_guess):
            guesses = [b for b in bin(num)[2:].zfill(num_guess)]
            resets = dict()
            for i, twS in enumerate(sorted(self.S)):
                if twS != ():
                    resets[twS] = False if guesses[i-1] == '0' else True
            for i, twR in enumerate(sorted(non_sink_R)):
                resets[twR] = False if guesses[i+len(self.S)-1] == '0' else True

            foundR = dict()
            for twR, infoR in non_sink_R.items():
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
            if all(foundR[twR] is not None for twR in foundR):
                return resets, foundR

    def buildCandidateOTA(self):
        """Construct candidate OTA from current information."""
        resets, foundR = self.findReset()
        # print(self.S)
        # print(self.R)

        # Mapping from timed words to location names.
        # Each path in S should correspond to a location.
        locations = dict()
        for i, twS in enumerate(sorted(self.S)):
            locations[twS] = str(i+1)
        locations['sink'] = str(len(self.S)+1)
        
        # Mapping from location and action to a list of transitions,
        # in the form of triples (time, reset, target).
        transitions = dict()
        for i in range(len(self.S)):
            name = str(i+1)
            transitions[name] = dict()
            for act in self.actions:
                transitions[name][act] = []

        # List of accept states
        accepts = []
        for twS in locations:
            if twS != 'sink' and self.S[twS].is_accept:
                accepts.append(locations[twS])
        
        # Fill in transitions using prefix in S.
        for twS in sorted(self.S):
            if twS != ():
                cur_loc = locations[twS]
                prev_loc = locations[twS[:-1]]
                start_time = self.S[twS[:-1]].getTimeVals(resets)
                transitions[prev_loc][twS[-1].action].append((start_time + twS[-1].time, resets[twS], cur_loc))
        
        # Fill in transitions using R.
        for twR in self.R:
            prev_loc = locations[twR[:-1]]
            start_time = self.S[twR[:-1]].getTimeVals(resets)
            if self.R[twR].is_sink:
                transitions[prev_loc][twR[-1].action].append((start_time + twR[-1].time, True, locations['sink']))
            else:
                cur_loc = locations[foundR[twR]]
                transitions[prev_loc][twR[-1].action].append((start_time + twR[-1].time, resets[twR], cur_loc))

        # print('locations', locations)
        # print('transitions', transitions)
        otaTrans = []
        for source in transitions:
            for action, trans in transitions[source].items():
                trans = sorted(trans)
                for i in range(len(trans)):
                    time, reset, target = trans[i]
                    if target is None:  # goes to sink
                        continue
                    if int(time) == time:
                        min_value, closed_min = int(time), True
                    else:
                        min_value, closed_min = int(time), False
                    if i < len(trans)-1:
                        time2, reset2, target2 = trans[i+1]
                        if int(time2) == time2:
                            max_value, closed_max = int(time2), False
                        else:
                            max_value, closed_max = int(time2), True
                        constraint = Interval(min_value, closed_min, max_value, closed_max)
                    else:
                        constraint = Interval(min_value, closed_min, '+', False)
                    otaTrans.append(OTATran(source, action, constraint, reset, target))

        location_objs = []
        for tw, loc in locations.items():
            if tw == 'sink':
                location_objs.append(Location(loc, False, False, True))
            else:
                location_objs.append(Location(loc, (tw == ()), self.S[tw].is_accept, self.S[tw].is_sink))
        candidateOTA = OTA(
            name=self.ota.name + '_',
            sigma=self.actions,
            locations=location_objs,
            trans=otaTrans,
            init_state='1',
            accept_states=accepts,
            sink_name=locations['sink'])

        return candidateOTA


def learn_ota(ota):
    """Overall learning loop."""
    learner = Learner(ota)
    assist_ota = buildAssistantOTA(ota)
    for i in range(5):
        candidate = learner.buildCandidateOTA()
        print(candidate)
        res, ctx = ota_equivalent(4, assist_ota, candidate)
        if res:
            print('Finished')
            break
        # print(res, ctx)
        ctx_path = ctx.find_path(assist_ota, candidate)
        print('Counterexample', ctx_path, ota.runTimedWord(ctx_path), candidate.runTimedWord(ctx_path))
        learner.addPath(ctx_path)
