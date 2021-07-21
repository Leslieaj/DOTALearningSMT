import pprint

from ota import Location, TimedWord, OTA, OTATran, buildAssistantOTA
from interval import Interval
from equivalence import ota_equivalent
import copy

import z3

def isSameRegion(t1, t2):
    """Check whether t1 and t2 lies in the same region. That is,
    if they are equal, or if they are both non-integers in the same
    interval (n, n+1).

    """
    return t1 == t2 or (int(t1) != t1 and int(t2) != t2 and int(t1) == int(t2))


def same_prefix_index(tw1, tw2):
    """
    Return the max same prefix index of two timed words. 
    
    """
    start_index = 0
    for i in range(min(len(tw1), len(tw2))):
        if tw1[:i+1] == tw2[:i+1]:
            start_index = i+1
        else:
            break

    return start_index

def isPrefix(tw1, tw2):
    """Determine whether tw1 is a prefix of tw2."""
    if len(tw1) > len(tw2):
        return False
    for i in range(len(tw1)):
        if tw1[i] != tw2[i]:
            return False

def generate_resets_pairs(tw1, tw2):
    """
    Return the possible reset pairs which respect to the principle of prefix-closed.
    """
    possible_pairs = []

    # the index from which two words become different
    start_index = same_prefix_index(tw1, tw2)
    # For the same prefixes, the reset information must be the same
    for i in range(start_index):
        possible_pairs.append((i, i))


    # find all possible combinations
    for i in range(start_index, len(tw1)+1):
        for j in range(start_index, len(tw2)+1):
            possible_pairs.append((i, j))

    return tuple(possible_pairs)

def set_row_reset(index, tw):
    reset = dict()
    for t in range(1, len(tw)+1):
        if t < index:
            continue
        elif t == index:
            reset[tw[:t]] = True
        else:
            reset[tw[:t]] = False
    return reset

def generate_row_resets(tw1, tw2):
    """
    Return a mapping from rows to reset settings.
    """
    resets = []
    possible_resets = generate_resets_pairs(tw1, tw2)
    for i, j in possible_resets:
        reset = dict()
        reset.update(set_row_reset(i, tw1))
        reset.update(set_row_reset(j, tw2))
        resets.append(reset)
    return tuple(resets)


def generate_row_resets_enhance(tw1, tw2):
    """
    Return a mapping from rows to reset settings which also pay attention to
    the reset of prefix before the true reset which is helpful to determine the whole time.
    """
    resets = []
    possible_resets = generate_resets_pairs(tw1, tw2)
    for i, j in possible_resets:
        reset = dict()
        reset.update(set_row_reset(i, tw1))
        reset.update(set_row_reset(j, tw2))
        # split tw1 and tw2 into the former part
        _tw1, _tw2 = tw1[:i-1], tw2[:j-1]
        _resets = generate_row_resets(_tw1, _tw2)
        for r in _resets:
            new_reset = copy.deepcopy(reset)
            new_reset.update(r)
            resets.append(new_reset)
    return resets


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
        self.R = dict()
        
        # add (a, 0) for each action in a to R
        for act in self.actions:
            tws = (TimedWord(act, 0), )
            res = self.ota.runTimedWord(tws)
            self.R[tws] = TestSequence(tws, res)

        # List of discriminator sequences
        self.E = []

        self.addPath(())

    def __str__(self):
        res = 'R:\n'
        for twR, info in sorted(self.R.items()):
            res += str(twR) + ': ' + str(info)
        res += 'E:\n'
        res += '\n'.join(','.join(str(tw) for tw in twE) for twE in self.E)
        return res

    def addPath(self, tws):
        """Add the given path tws (and its prefixes) to R.
        
        Starting from the head, it keeps adding longer prefixes until reaching
        the sink.

        """
        tws = tuple(tws)
        for i in range(len(tws)+1):
            cur_tws = tws[:i]

            cur_res = self.ota.runTimedWord(cur_tws)
            if cur_tws not in self.R:
                self.R[cur_tws] = TestSequence(cur_tws, cur_res)
                if cur_res != -1:
                    for act in self.actions:
                        cur_tws_act = tws + (TimedWord(act, 0),)
                        cur_res_act = self.ota.runTimedWord(cur_tws_act)
                        self.R[cur_tws_act] = TestSequence(cur_tws_act, cur_res_act)
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

    def encodeReset(self, reset, resets_var):
        """Encode the reset information into formula.
        
        Note: the formula only contains rows which start from the last reset.
        Example: suppose a sequence
        (a, t1, ⊥)(b, t2, ⊥)(c, t3, ⊤)(d, t4, ⊤)
        then the formula only contains the variables which represent
        r_3: (a, t1, ⊥)(b, t2, ⊥)(c, t3, ⊤),
        r_4: (a, t1, ⊥)(b, t2, ⊥)(c, t3, ⊤)(d, t4, ⊤)
        since (a, t1) and (a, t1)(b, t2) 's reset cannot influence the whole time.
        """
        formula = []
        for row, r in reset.items():
            if r:
                formula.append(resets_var[row])
            else:
                formula.append(z3.Not(resets_var[row]))
        assert len(formula) > 0, "Invalid resets!"
        return z3.And(formula)

    def differentStateUnderReset(self, states_var, resets_var):
        """Constraint 1: find different states under some reset settings.
        
        states_var - mapping from rows to states variables
        resets_var - mapping from rows to resets variables

        Return a formula encoding the relation.
        """
        formula = []
        
        for tw1 in self.R:
            for tw2 in self.R:
                possible_resets = generate_row_resets(tw1, tw2)
                for reset in possible_resets:
                    if self.findDistinguishingSuffix(self.R[tw1], self.R[tw2], reset) is not None:
                        f = z3.Implies(self.encodeReset(reset, resets_var), states_var[tw1] != states_var[tw2])
                        formula.append(f)

        if len(formula) > 0:
            return z3.And(formula)
        else:
            return True


    def noForbiddenPair(self, non_sink_row, states_var, resets_var):
        """Constraint 2: for any tow rows R1 + (a, t1) and R2 + (a, t2), 
        if states[R1] = states[R2], and they are in the same time interval,
        if the two rows are at same states, then they should have same reset settings.        
        """
        formula = []
        for tw1 in non_sink_row:
            for tw2 in non_sink_row:
                if tw1 != () and tw2 != () and tw1[-1].action == tw2[-1].action:
                    possible_resets = generate_row_resets_enhance(tw1, tw2)
                    for reset in possible_resets:
                        if self.findDistinguishingSuffix(non_sink_row[tw1], non_sink_row[tw2], reset) is None: # maybe in the same states
                            time_val1 = non_sink_row[tw1[:-1]].getTimeVal(reset)
                            time_val2 = non_sink_row[tw1[:-1]].getTimeVal(reset)
                            if isSameRegion(time_val1+tw1[-1].time, time_val2+tw2[-1].time) and \
                                reset[tw1] != reset[tw2]:
                                f = z3.Implies(states_var[tw1] == states_var[tw2], z3.Not(self.encodeReset(reset, resets_var)))
                                formula.append(f)

        if formula:
            return z3.And(formula)
        else:
            return True

    def noInvalidRow(self, states_var, resets_var):
        """Constraint 3: for any two rows R + (a, t1), R + (a, t2), if they are
        in the same time interval, we must ensure that they go into the same state.
        """
        formulas = []
        for tw1 in self.R:
            for tw2 in self.R:
                # the condition could be more intensive: |t1 - t2| < 1
                if tw1 != () and tw2 != () and tw1[:-1] == tw2[:-1] and tw1[-1].action and tw2[-1].action\
                        and abs(tw1[-1].time - tw2[-1].time < 1):
                    possible_resets = generate_row_resets_enhance(tw1, tw2)
                    for reset in possible_resets:
                        if self.findDistinguishingSuffix(self.R[tw1], self.R[tw2], reset) is not None:
                            time_val1 = self.R[tw1[:-1]].getTimeVal(reset)
                            time_val2 = self.R[tw2[:-1]].getTimeVal(reset)
                            if isSameRegion(time_val1+tw1[-1].time, time_val2+tw2[-1].time):
                                f = self.encodeReset(reset, resets_var)
                                formulas.append(z3.Not(f))

        if formulas:
            return z3.And(formulas)
        else:
            return True

    def checkConsistency(self, states_var, resets_var):
        """Constraint 4: for any two rows R1 + (a, t1), R2 + (a, t2). If R1 and R2 are
        in the same states, and under the current reset settings these two rows are in
        the same time interval, then their states should also be same."""
        formulas = []
        for tw1 in self.R:
            for tw2 in self.R:
                if tw1 == (TimedWord('a', 1), TimedWord('b', 3)) and tw2 == (TimedWord('a', 1), TimedWord('b', 3), TimedWord('b', 0)):
                    print(tw1)
                if tw1 != () and tw2 != () and tw1[-1].action == tw2[-1].action:
                    possible_resets = generate_row_resets_enhance(tw1, tw2)
                    for reset in possible_resets:
                        if self.findDistinguishingSuffix(self.R[tw1[:-1]], self.R[tw2[:-1]], reset) is None: # tw[:-1] and tw2[:-1] may in the same states
                            time_val1 = self.R[tw1[:-1]].getTimeVal(reset)
                            time_val2 = self.R[tw2[:-1]].getTimeVal(reset)
                            if isSameRegion(time_val1+tw1[-1].time, time_val2+tw2[-1].time):
                                suffix = self.findDistinguishingSuffix(self.R[tw1], self.R[tw2], reset)
                                if suffix is not None:
                                    f = z3.Implies(states_var[tw1[:-1]] == states_var[tw2[:-1]], z3.Not(self.encodeReset(reset, resets_var)))
                                    formulas.append(f)
                                    new_E = (TimedWord(tw1[-1].action, min(tw1[-1].time, tw2[-1].time)),) + suffix
                                    if new_E in self.E:
                                        raise ValueError
                                    self.E.append(new_E)

        if formulas:
            return z3.And(formulas)
        else:
            return True

    def findReset(self):
        """Find a valid setting of resets and states.
        
        Return a tuple (resets, states). 

        state_num - the possible number of states
        """
        # find non_sink rows
        non_sink_R = dict((twR, infoR) for twR, infoR in self.R.items()
                          if not infoR.is_sink)

        # Give each row a state variable and a reset variable
        states_var, resets_var = dict(), dict()

        for i, row in enumerate(self.R):
            states_var[row] = z3.Int("s_%d" % (i+1))
            resets_var[row] = z3.Bool("r_%d" % (i+1))

        var_states = dict((v, k) for k, v in states_var.items())
        var_resets = dict((v, k) for k, v in resets_var.items())

        # # Limit number of states
        # state_constraint = [z3.And(s>=1, s<=state_num) for s in states_var]
        # s.add(state_constraint)

        # Constraint 1: if two rows behaves differently under some reset settings, 
        # then we can conclude that their states are not same.
        constraint1 = self.differentStateUnderReset(states_var, resets_var)
        constraint2 = self.noForbiddenPair(non_sink_R, states_var, resets_var)
        constraint3 = self.noInvalidRow(states_var, resets_var)
        constraint4 = self.checkConsistency(states_var, resets_var)

        result = "unsat"
        for i in range(1, len(non_sink_R)+1):
            constraint5 = []
            for s, row in var_states.items():
                if self.R[row].is_sink:
                    constraint5.append(s == i + 1)
                else:
                    constraint5.append(z3.And(s>=1, s<=i))
            constraint5 = z3.And(constraint5)
            s = z3.Solver()
            s.add(constraint1, constraint2, constraint3, constraint4, constraint5)
            if str(s.check()) == "sat":
                result = "sat"
                break
            else:
                continue

        if result == "unsat": # why?
            return None, None

        model = s.model()
        print("model", model)
        resets, states = dict(), dict()

        for v in model:
            if isinstance(model[v], z3.ArithRef):
                states[var_states[z3.Int(str(v))]] = str(model[v])
            elif isinstance(model[v], z3.BoolRef):
                resets[var_resets[z3.Bool(str(v))]] = bool(model[v])
            else:
                raise NotImplementedError

        # set all reset variables to True which do not exist in constraints
        for v, row in var_resets.items():
            if row not in resets:
                resets[row] = True

        states["sink"] = str(i + 1)

        return resets, states


    def buildCandidateOTA(self, resets, states):
        """Construct candidate OTA from current information.

        resets - guessed reset information for each entry in R.
        states - guessed state mapping for each entry in R.
        """
        states_num = int(states["sink"])

        # Mapping from location, action and time to transitions,
        # in the form of (reset, target)
        # transitions: states -> action -> time -> (reset, state)
        transitions = dict()
        for i in range(states_num):
            name = str(i+1)
            transitions[name] = dict()
            for act in self.actions:
                transitions[name][act] = dict()

        # List of accept states
        accepts = set()
        for row in states:
            if row != 'sink' and self.R[row].is_accept:
                accepts.add(states[row])

        accepts = list(accepts)
        # Fill in transitions using R.
        for twR in sorted(self.R):
            if twR == ():
                continue
            
            prev_loc = states[twR[:-1]]
            start_time = self.R[twR[:-1]].getTimeVal(resets)
            trans_time = start_time + twR[-1].time
            if self.R[twR].is_sink:
                cur_reset, cur_loc = True, states['sink']
            else:
                cur_reset, cur_loc = resets[twR], states[twR]

            if trans_time in transitions[prev_loc][twR[-1].action] and\
                    (cur_reset, cur_loc) != transitions[prev_loc][twR[-1].action][trans_time]:
                print('When adding transition for', twR)
                raise AssertionError('Conflict at %s (%s, %s)' % (prev_loc, twR[-1].action, trans_time))
            transitions[prev_loc][twR[-1].action][trans_time] = cur_reset, cur_loc

        # Sink transitions
        for act in self.actions:
            transitions[states["sink"]][act][0] = (True, states["sink"])

        # From the dictionary of transitions, form the list otaTrans
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

        # Form the location objects
        location_objs = []
        for tw, loc in states.items():
            if tw == "sink":
                location_objs.append(Location(loc, False, False, True))
            else:
                location_objs.append(Location(loc, (tw==()), self.R[tw].is_accept, self.R[tw].is_sink))

        candidateOTA = OTA(
            name=self.ota.name + '_',
            sigma=self.actions,
            locations=location_objs,
            trans=otaTrans,
            init_state='1',
            accept_states=accepts,
            sink_name=states['sink'])

        return candidateOTA


def learn_ota(ota, limit=30, verbose=True):
    """Overall learning loop."""
    learner = Learner(ota)
    assist_ota = buildAssistantOTA(ota)
    for i in range(1, limit):
        print("Step", i)
        if i == 5:
            i
        resets, states = learner.findReset()

        if verbose:
            print(learner)

        if resets is None:
            # No possible choice of resets with the current S.
            raise NotImplementedError

        if verbose:
            print("resets and states:")
            for tws, v in resets.items():
                print("  %s: %s %s" % (",".join(str(tw) for tw in tws), v, states[tws]))

        candidate = learner.buildCandidateOTA(resets, states)
        res, ctx = ota_equivalent(10, assist_ota, candidate)
        if not res and verbose:
            print(candidate)
        if res:
            print(candidate)
            print("Finished in %s steps " % i)
            break

        ctx_path = ctx.find_path(assist_ota, candidate)
        if verbose:
            print("Counterexample", ctx_path, ota.runTimedWord(ctx_path), candidate.runTimedWord(ctx_path))
        learner.addPath(ctx_path)
