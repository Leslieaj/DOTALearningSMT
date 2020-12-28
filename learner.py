# Data structure for the learner.

import pprint

from ota import Location, TimedWord, OTA, OTATran, buildAssistantOTA
from interval import Interval
from equivalence import ota_equivalent


def isSameRegion(t1, t2):
    """Check whether t1 and t2 lies in the same region. That is,
    if they are equal, or if they are both non-integers in the same
    interval (n, n+1).

    """
    return t1 == t2 or (int(t1) != t1 and int(t2) != t2 and int(t1) == int(t2))


class TestSequence:
    """Represents data for a single test sequence."""
    def __init__(self, tws, res):
        """Initialize data for a test sequence.

        tws - list(TimedWord)
        res - 1, 0, or -1, indicating accept, non-accept, and sink.

        Keeps a dictionary mapping suffixes to test results.

        """
        self.tws = tuple(tws)

        self.is_accept = (res == 1)
        self.is_sink = (res == -1)
        self.info = dict()

    def __str__(self):
        if self.is_accept:
            res = "Accept\n"
        elif self.is_sink:
            res = "Sink\n"
        else:
            res = "Non-accept\n"
        for tws, val in sorted(self.info.items()):
            res += '  %s: %s\n' % (','.join(str(tw) for tw in tws), val)
        return res

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
        """Return the set of possible values of the clock at the end of tws.

        This considers all possible values of resets. Starting from
        the end, find all possible sums of suffixes.

        """
        vals = {0}
        cur_time = 0
        for tw in reversed(self.tws):
            if tw.time > 0:
                cur_time += tw.time
                vals.add(cur_time)
        return vals

    def getTimeVal(self, resets):
        """Given a choice of resets, find the value of time at the end.
        
        resets - dict(TimedWord, bool).
        Mapping from timed words to whether guessing a reset at its end.

        """
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

        # S and R are test sequences that are internal and at the boundary.
        self.S = dict()
        self.R = dict()

        # List of discriminator sequences
        self.E = []

        self.addPath(())
        self.addToS(())

    def __str__(self):
        res = 'S:\n'
        for twS, info in sorted(self.S.items()):
            res += str(twS) + ': ' + str(info)
        res += 'R:\n'
        for twR, info in sorted(self.R.items()):
            res += str(twR) + ': ' + str(info)
        res += 'E:\n'
        res += '\n'.join(','.join(str(tw) for tw in twE) for twE in self.E)
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
        """Add the given path tws (and its prefixes) to R.
        
        Starting from the head, it keeps adding longer prefixes until reaching
        the sink.

        """
        tws = tuple(tws)
        for i in range(len(tws)+1):
            cur_tws = tws[:i]

            cur_res = self.ota.runTimedWord(cur_tws)
            if cur_tws not in self.S and cur_tws not in self.R:
                self.R[cur_tws] = TestSequence(cur_tws, cur_res)
            if cur_res == -1:  # stop when already reached sink
                break

    def findDistinguishingSuffix(self, info1, info2, resets):
        """Check whether the two timed words are equivalent.
        
        If equivalent according to the current E, return None.

        Otherwise, return the distinguishing suffix (which works by shifting
        the first timed word to align the clock).

        """
        if info1.is_accept != info2.is_accept or info1.is_sink != info2.is_sink:
            return tuple()  # empty suffix is distinguishing

        time1 = info1.getTimeVal(resets)
        time2 = info2.getTimeVal(resets)

        for twE in self.E:
            if time1 == time2:
                res1 = info1.testSuffix(self.ota, twE)
                res2 = info2.testSuffix(self.ota, twE)
            elif time1 < time2:
                shift = time2 - time1
                res1 = info1.testSuffix(self.ota, twE, shift)
                res2 = info2.testSuffix(self.ota, twE)
            else:  # time1 > time2
                shift = time1 - time2
                res1 = info1.testSuffix(self.ota, twE)
                res2 = info2.testSuffix(self.ota, twE, shift)
            if res1 != res2:
                return twE

        return None

    def findReset(self):
        """Find a valid setting of resets.
        
        Returns a tuple (resets, foundR). If success, then resets is a
        dictionary mapping from nonempty keys in S and R to booleans, and
        foundR is a mapping from keys in S and R to keys in S (or the sink)
        that can correspond to the same location.

        If fails, then resets is None.

        """
        # Take a guess for each nonempty key in S and each key in R that
        # is not a sink.
        non_sink_R = dict((twR, infoR) for twR, infoR in self.R.items()
                          if not infoR.is_sink)
        num_guess = len(self.S) + len(non_sink_R) - 1

        # For each non-sink R, find the number of times with match in S.
        foundR_count = dict()
        for twR in non_sink_R:
            foundR_count[twR] = 0

        # Iterate over the guesses.
        for num in range(2 ** num_guess):
            # List of booleans corresponding to the current guess.
            guesses = [b for b in bin(num)[2:].zfill(num_guess)]

            # Get the dictionary mapping timed words to guesses.
            resets = dict()
            for i, twS in enumerate(sorted(self.S)):
                if twS != ():
                    resets[twS] = False if guesses[i-1] == '0' else True
            for i, twR in enumerate(sorted(non_sink_R)):
                resets[twR] = False if guesses[i+len(self.S)-1] == '0' else True

            # Form the mapping from S and R to S. First, fill in the
            # obvious cases.
            foundR = dict()
            for twS in self.S:
                foundR[twS] = twS
            for twR, infoR in self.R.items():
                if infoR.is_sink:
                    foundR[twR] = 'sink'

            # Now consider the remaining cases. For each R, and for each S,
            # find the time values under the current guess of resets. Then
            # compare using the timed words in E after performing the required
            # shifts.
            for twR, infoR in non_sink_R.items():
                foundR[twR] = None
                for twS, infoS in self.S.items():
                    suffix = self.findDistinguishingSuffix(infoR, infoS, resets)

                    if suffix is None:
                        foundR[twR] = twS
                        foundR_count[twR] += 1
                        break

            # Check if all rows in R can be mapped
            if not all(foundR[twR] is not None for twR in foundR):
                continue

            # Check if the mapping contains forbidden pairs
            if not self.checkForbiddenPairs(resets, foundR):
                continue

            # Check if the mapping contains invalid rows
            if not self.checkInvalidRow(resets, foundR):
                continue

            # Check consistency of the resulting table
            newE = self.checkConsistent(resets, foundR)
            if newE:
                self.E.append(newE)
                continue

            # After all validity checks, return results
            return resets, foundR

        # Cannot find a guess.
        return None, foundR_count

    def checkForbiddenPairs(self, resets, foundR):
        """Check validity of reset information.

        The main check is that: for any R1 + (a, t1) and R2 + (a, t2),
        if foundR[R1] == foundR[R2], and the actions and times are the same,
        then the reset information should be the same.

        Returns whether the reset information is valid according to the above
        criteria.

        """
        rows = dict()
        for tws in self.S:
            rows[tws] = self.S[tws]
        for tws in self.R:
            if not self.R[tws].is_sink:
                rows[tws] = self.R[tws]

        for tw1 in rows:
            for tw2 in rows:
                if tw1 != () and tw2 != () and resets[tw1] != resets[tw2] and \
                    foundR[tw1[:-1]] == foundR[tw2[:-1]] and tw1[-1].action == tw2[-1].action:
                    time_val1 = rows[tw1[:-1]].getTimeVal(resets)
                    time_val2 = rows[tw2[:-1]].getTimeVal(resets)
                    if isSameRegion(tw1[-1].time + time_val1, tw2[-1].time + time_val2):
                        return False

        return True

    def checkInvalidRow(self, resets, foundR):
        """Check whether there are invalid rows.

        An invalid row is given by the fact that it can be distinguished from
        itself under the given resets.

        """
        rows = dict()
        for tws in self.S:
            rows[tws] = self.S[tws]
        for tws in self.R:
            rows[tws] = self.R[tws]
        for tw1 in rows:
            for tw2 in rows:
                if tw1 != () and tw2 != () and foundR[tw1] != foundR[tw2] and \
                    tw1[:-1] == tw2[:-1] and tw1[-1].action == tw2[-1].action:
                    time_val1 = rows[tw1[:-1]].getTimeVal(resets)
                    time_val2 = rows[tw2[:-1]].getTimeVal(resets)
                    if isSameRegion(tw1[-1].time + time_val1, tw2[-1].time + time_val2):
                        return False

        return True

    def checkConsistent(self, resets, foundR):
        """Check whether the table is consistent.

        resets - guessed reset information for each entry in S and R.
        foundR - mapping from rows in S and R to rows in S.

        The consistency check is as follows: for each pair of nonempty keys
        in S and R, if their immediate prefix is assigned the same, and the
        last action and time are the same, then they should be assigned the
        same.

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
                    time_val1 = rows[tw1[:-1]].getTimeVal(resets)
                    time_val2 = rows[tw2[:-1]].getTimeVal(resets)
                    if isSameRegion(tw1[-1].time + time_val1, tw2[-1].time + time_val2):
                        # Witness for inconsistency, return new value of E
                        suffix = self.findDistinguishingSuffix(rows[tw1], rows[tw2], resets)
                        assert suffix is not None, 'No distinguishing suffix found'
                        newE = (TimedWord(tw1[-1].action, min(tw1[-1].time, tw2[-1].time)),) + suffix
                        if newE in self.E:
                            print('resets', resets)
                            print('tw1', tw1)
                            print('tw2', tw2)
                            print('time1', time_val1)
                            print('time2', time_val2)
                            print('suffix', suffix)
                            print('newE', newE)
                            raise AssertionError('Repeated newE.')
                        # print('Add new E:', newE)
                        return newE

        return None

    def buildCandidateOTA(self, resets, foundR):
        """Construct candidate OTA from current information
        
        resets - guessed reset information for each entry in S and R.
        foundR - mapping from rows in S and R to rows in S (or the sink).
        
        """
        # Mapping from timed words to location names.
        # Each path in S should correspond to a location.
        locations = dict()
        for i, twS in enumerate(sorted(self.S)):
            locations[twS] = str(i+1)
        locations['sink'] = str(len(self.S)+1)
        
        # Mapping from location, action and time to transitions,
        # in the form of (reset, target).
        transitions = dict()
        for i in range(len(self.S)+1):
            name = str(i+1)
            transitions[name] = dict()
            for act in self.actions:
                transitions[name][act] = dict()

        # List of accept states
        accepts = []
        for twS in locations:
            if twS != 'sink' and self.S[twS].is_accept:
                accepts.append(locations[twS])
        
        # Fill in transitions using prefix in S. For each nonempty entry
        # in S, find its immediate predecessor.
        for twS in sorted(self.S):
            if twS == ():
                continue

            cur_loc = locations[twS]
            assert twS[:-1] in locations, 'S is not prefix closed'
            prev_loc = locations[twS[:-1]]
            start_time = self.S[twS[:-1]].getTimeVal(resets)
            trans_time = start_time + twS[-1].time
            if trans_time in transitions[prev_loc][twS[-1].action] and \
                (resets[twS], cur_loc) != transitions[prev_loc][twS[-1].action][trans_time]:
                print('When adding transition for', twS)
                raise AssertionError('Conflict at %s %s %s' % (prev_loc, twS[-1].action, trans_time))
            transitions[prev_loc][twS[-1].action][trans_time] = (resets[twS], cur_loc)
 
        # Fill in transitions using R.
        for twR in self.R:
            if twR[:-1] in locations:
                prev_loc = locations[twR[:-1]]
                start_time = self.S[twR[:-1]].getTimeVal(resets)
            else:
                prev_loc = locations[foundR[twR[:-1]]]
                start_time = self.R[twR[:-1]].getTimeVal(resets)
            
            trans_time = start_time + twR[-1].time
            if self.R[twR].is_sink:
                cur_reset, cur_loc = True, locations['sink']
            else:
                cur_reset, cur_loc = resets[twR], locations[foundR[twR]]

            if trans_time in transitions[prev_loc][twR[-1].action] and \
                (cur_reset, cur_loc) != transitions[prev_loc][twR[-1].action][trans_time]:
                print('When adding transition for', twR)
                raise AssertionError('Conflict at %s (%s, %s)' % (prev_loc, twS[-1].action, trans_time))
            transitions[prev_loc][twR[-1].action][trans_time] = cur_reset, cur_loc

        # Sink transitions
        for act in self.actions:
            transitions[locations['sink']][act][0] = (True, locations['sink'])

        # From the dictionary of transitions, form the list otaTrans.
        otaTrans = []
        for source in transitions:
            for action, trans in transitions[source].items():
                # Sort and remove duplicates
                trans = sorted((time, reset, target) for time, (reset, target) in trans.items())
                trans_new = [trans[0]]
                for i in range(1, len(trans)):
                    time, reset, target = trans[i]
                    prev_time, prev_reset, prev_target = trans[i-1]
                    if reset != prev_reset or target != prev_target:
                        trans_new.append(trans[i])
                trans = trans_new

                # Change to otaTrans.
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

        # Form the Location objects.
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


def learn_ota(ota, limit=15, verbose=True):
    """Overall learning loop."""
    learner = Learner(ota)
    assist_ota = buildAssistantOTA(ota)
    for i in range(1, limit):
        print ('Step', i)
        resets, foundR = learner.findReset()

        if verbose:
            print(learner)

        if resets is None:
            # No possible choice of resets with the current S.
            # Find an element in foundR with small count and to add to S.
            print(foundR)
            min_key, min_count = None, None
            for twR, count in sorted(foundR.items()):
                if min_count is None or count < min_count:
                    min_key, min_count = twR, count
            assert min_key is not None

            # Add the shortest prefix of twR not currently in S.
            for i in range(len(min_key)+1):
                if min_key[:i] not in learner.S:
                    if verbose:
                        print('No possible reset found. Add %s to S' % (','.join(str(tw) for tw in min_key[:i])))
                    learner.addToS(min_key[:i])
                    break
        else:
            # Found possible choice of resets.
            if verbose:
                print('resets:')
                for tws, v in resets.items():
                    print('  %s: %s' % (','.join(str(tw) for tw in tws), v))
                print('foundR:')
                for tws, target in foundR.items():
                    if tws != target and target != 'sink':
                        print('  %s -> %s' % (','.join(str(tw) for tw in tws),
                                                ','.join(str(tw) for tw in target) if target else '()'))
                print()

            candidate = learner.buildCandidateOTA(resets, foundR)
            res, ctx = ota_equivalent(10, assist_ota, candidate)
            if not res and verbose:
                print(candidate)
            if res:
                print(candidate)
                print('Finished in %s steps' % i)
                break

            ctx_path = ctx.find_path(assist_ota, candidate)
            if verbose:
                print('Counterexample', ctx_path, ota.runTimedWord(ctx_path), candidate.runTimedWord(ctx_path))
            learner.addPath(ctx_path)
