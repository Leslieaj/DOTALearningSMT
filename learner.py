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
        if self.is_accept:
            return "Accept, Info: %s" % self.info
        elif self.is_sink:
            return "Sink, Info: %s" % self.info
        else:
            return "Non-accept, Info: %s" % self.info

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
        if tws2 not in self.info:
            self.info[tws2] = ota.runTimedWord(tws)

        return self.info[tws2]

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
        self.addToS(())

    def __str__(self):
        res = 'S:\n'
        for twS, info in self.S.items():
            res += str(twS) + ': ' + str(info) + '\n'
        res += 'R:\n'
        for twR, info in self.R.items():
            res += str(twR) + ': ' + str(info) + '\n'
        return res

    def addToS(self, tws):
        """Add the given path (which should already be in R) onto S.
        
        This additionally adds tws + (a, 0) to R for each action a.

        """
        assert tws not in self.S and tws in self.R, 'addToS: tws should be in R and not in S'
        self.S[tws] = self.R[tws]
        del self.R[tws]

        # If tws does not go to sink, add tws + (a, 0) to R
        if self.ota.runTimedWord(tws) != -1:
            for act in self.actions:
                cur_tws = tws + (TimedWord(act, 0),)
                if cur_tws not in self.R:
                    cur_res = self.ota.runTimedWord(cur_tws)
                    self.R[cur_tws] = TestSequence(cur_tws, cur_res)

    def addPath(self, tws):
        """Add the given path tws (and all its prefixes) to R."""
        tws = tuple(tws)
        for i in range(len(tws)+1):
            cur_tws = tws[:i]

            if cur_tws not in self.S and cur_tws not in self.R:
                cur_res = self.ota.runTimedWord(cur_tws)
                self.R[cur_tws] = TestSequence(cur_tws, cur_res)
                if cur_res == -1:  # stop when already reached sink
                    break
        
    def findReset(self):
        non_sink_R = dict((twR, infoR) for twR, infoR in self.R.items()
                          if not infoR.is_sink)
        num_guess = len(self.S) + len(non_sink_R) - 1

        # Record whether it is possible to find a match in S.
        foundR_all = dict()
        for twR in non_sink_R:
            foundR_all[twR] = None

        for num in range(2 ** num_guess):
            guesses = [b for b in bin(num)[2:].zfill(num_guess)]
            resets = dict()
            for i, twS in enumerate(sorted(self.S)):
                if twS != ():
                    resets[twS] = False if guesses[i-1] == '0' else True
            for i, twR in enumerate(sorted(non_sink_R)):
                resets[twR] = False if guesses[i+len(self.S)-1] == '0' else True

            foundR = dict()
            for twS in self.S:
                foundR[twS] = twS
            for twR, infoR in self.R.items():
                if infoR.is_sink:
                    foundR[twR] = 'sink'
            for twR, infoR in non_sink_R.items():
                foundR[twR] = None
                time_R = infoR.getTimeVals(resets)
                for twS, infoS in self.S.items():
                    time_S = infoS.getTimeVals(resets)
                    is_same = True
                    if infoR.is_accept != infoS.is_accept:
                        is_same = False

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
                            res_S = infoS.testSuffix(self.ota, twE, shift_S)
                        if res_R != res_S:
                            is_same = False
                            break
                    if is_same:
                        foundR[twR] = twS
                        foundR_all[twR] = twS
                        break

            if all(foundR[twR] is not None for twR in foundR):
                return resets, foundR

        # failed
        return None, foundR_all

    def checkConsistent(self, resets, foundR):
        """Check whether the table is consistent.

        resets - guessed reset information for each entry in S and R.
        foundR - mapping from rows in R to rows in S.

        """
        rows = dict()
        for tws in self.S:
            rows[tws] = self.S[tws]
        for tws in self.R:
            rows[tws] = self.R[tws]
        for tw1 in rows:
            for tw2 in rows:
                if tw1 != () and tw2 != () and foundR[tw1] != foundR[tw2] and \
                    foundR[tw1[:-1]] == foundR[tw2[:-1]] and tw1[-1].action == tw2[-1].action:
                    time_val1 = rows[tw1[:-1]].getTimeVals(resets)
                    time_val2 = rows[tw2[:-1]].getTimeVals(resets)
                    if tw1[-1].time + time_val1 == tw2[-1].time + time_val2:
                        # Witness for inconsistency, return new value of E
                        if self.ota.runTimedWord(tw1) != self.ota.runTimedWord(tw2):
                            newE = ()
                        else:
                            newE = None
                            for twE in self.E:
                                if time_val1 == time_val2:
                                    res1 = rows[tw1].testSuffix(self.ota, twE)
                                    res2 = rows[tw2].testSuffix(self.ota, twE)
                                elif time_R < time_S:
                                    shift_R = time_S - time_R
                                    res1 = rows[tw1].testSuffix(self.ota, twE, shift_R)
                                    res2 = rows[tw2].testSuffix(self.ota, twE)
                                else:  # time_R > time_S
                                    shift_S = time_R - time_S
                                    res1 = rows[tw1].testSuffix(self.ota, twE)
                                    res2 = rows[tw2].testSuffix(self.ota, twE, shift_S)
                                if res1 != res2:
                                    newE = twE
                                    break
                        assert newE is not None
                        newE = (TimedWord(tw1[-1].action, min(tw1[-1].time, tw2[-1].time)),) + newE
                        return newE

        return None

    def buildCandidateOTA(self, resets, foundR):
        """Construct candidate OTA from current information
        
        resets - guessed reset information for each entry in S and R.
        foundR - mapping from rows in R to rows in S.
        
        """
        # Mapping from timed words to location names.
        # Each path in S should correspond to a location.
        locations = dict()
        for i, twS in enumerate(sorted(self.S)):
            locations[twS] = str(i+1)
        locations['sink'] = str(len(self.S)+1)
        
        # Mapping from location and action to a list of transitions,
        # in the form of triples (time, reset, target).
        transitions = dict()
        for i in range(len(self.S)+1):
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
                if twS[:-1] in locations:
                    prev_loc = locations[twS[:-1]]
                    start_time = self.S[twS[:-1]].getTimeVals(resets)
                else:
                    prev_loc = locations[foundR[twS[:-1]]]
                    start_time = self.R[twS[:-1]].getTimeVals(resets)
                transitions[prev_loc][twS[-1].action].append((start_time + twS[-1].time, resets[twS], cur_loc))
        
        # Fill in transitions using R.
        for twR in self.R:
            if twR[:-1] in locations:
                prev_loc = locations[twR[:-1]]
                start_time = self.S[twR[:-1]].getTimeVals(resets)
            else:
                prev_loc = locations[foundR[twR[:-1]]]
                start_time = self.R[twR[:-1]].getTimeVals(resets)
            if self.R[twR].is_sink:
                transitions[prev_loc][twR[-1].action].append((start_time + twR[-1].time, True, locations['sink']))
            else:
                cur_loc = locations[foundR[twR]]
                transitions[prev_loc][twR[-1].action].append((start_time + twR[-1].time, resets[twR], cur_loc))

        # Sink transitions
        for act in self.actions:
            transitions[locations['sink']][act].append((0, True, locations['sink']))

        # print('locations', locations)
        otaTrans = []
        for source in transitions:
            for action, trans in transitions[source].items():
                trans = sorted(trans)

                # Remove duplicates
                trans_new = [trans[0]]
                for i in range(1, len(trans)):
                    time, reset, target = trans[i]
                    ptime, preset, ptarget = trans[i-1]
                    if reset != preset or target != ptarget:
                        trans_new.append(trans[i])
                trans = trans_new

                # print('transitions:', source, action, trans)
                for i in range(len(trans)):
                    time, reset, target = trans[i]                            
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
    for i in range(10):
        while True:
            resets, foundR = learner.findReset()
            print(learner)
            print('resets', resets)
            print('foundR', dict((k,v) for k, v in foundR.items() if k != v and v != 'sink'))
            if resets is None:
                hasAddToS = False
                for twR in foundR:
                    if foundR[twR] is None:
                        learner.addToS(twR)
                        hasAddToS = True
                        break
                assert hasAddToS
            else:
                newE = learner.checkConsistent(resets, foundR)
                if newE is None:
                    break
                else:
                    learner.E.append(newE)

        candidate = learner.buildCandidateOTA(resets, foundR)
        print(candidate)
        res, ctx = ota_equivalent(10, assist_ota, candidate)
        if res:
            print('Finished')
            break
        # print(res, ctx)
        ctx_path = ctx.find_path(assist_ota, candidate)
        print('Counterexample', ctx_path, ota.runTimedWord(ctx_path), candidate.runTimedWord(ctx_path))
        learner.addPath(ctx_path)
