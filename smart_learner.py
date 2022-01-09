import pprint
from ota import Location, TimedWord, OTA, OTATran, buildAssistantOTA, OTAToJSON
from interval import Interval
from equivalence import ota_equivalent
import copy
import z3
import time

def isSameRegion(t1, t2):
    """Check whether t1 and t2 lies in the same region. That is,
    if they are equal, or if they are both non-integers in the same
    interval (n, n+1).

    """
    return t1 == t2 or (int(t1) != t1 and int(t2) != t2 and int(t1) == int(t2))

def generate_resets_pairs(tw1, tw2):
    possible_pairs = []
    for i in range(len(tw1)+1):
        for j in range(len(tw2)+1):
            possible_pairs.append((i, j))

    return tuple(possible_pairs)

def set_row_reset(index, tw):
    """Given index as the last reset point in tw, return the implied
    reset information: True for the prefix ending at index, and False
    for all longer prefixes.
    
    """
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
    """Given a pair of timed words, iterate over all choices of last
    reset, and collect together the corresponding reset information.
    
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
    """Given a pair of timed words, iterate over all choices of last
    *two* resets, and collect together the corresponding reset
    information.

    """
    resets = []
    possible_resets = generate_resets_pairs(tw1, tw2)

    for i, j in possible_resets:
        # split tw1 and tw2 into the former part
        _tw1, _tw2 = tw1[:i-1], tw2[:j-1]
        _resets = generate_row_resets(_tw1, _tw2)
        for r in _resets:
            reset = dict()
            reset.update(set_row_reset(i, tw1))
            reset.update(set_row_reset(j, tw2))
            reset.update(r)
            if reset not in resets:
                resets.append(reset)
    return resets


class TestSequence:
    """Represents data for a single test sequence."""
    def __init__(self, tws, res):
        """Initialize data for a test sequence.

        tws - list(TimedWord)
        res - 1, 0, or -1, indicating accept, non-accept, and sink.

        Keeps a dictionary info, mapping suffixes to test results.

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

        # R stores sequences that are internal and at the boundary.
        self.R = dict()

        # S stores sequences which represent different states
        self.S = dict()

        # extra_S stores those rows that are not guaranteed to be different
        # from S, but are needed as representatives for some resets.
        self.extra_S = dict()

        # Mapping from rows to states variables
        self.state_name = dict()

        # Mapping from rows to resets and states name
        self.reset_name = dict()

        # List of discriminator sequences
        self.E = []

        # Store the formulas in constraint1:
        # - If two rows can be distinguished under a given reset, then that
        #   reset implies the state_name of the two rows are not the same.
        self.constraint1_formula = []

        # Store triples of the form (tw1, tw2, reset):
        # - The two rows tw1 and tw2 cannot be distinguished by the current
        #   suffixes, under the given reset.
        self.constraint1_triple = []

        # Store the formulas in constraint 2: 
        self.constraint2_formula = []
        # Store the (tw1, tw2, reset) triple which cannot be disti
        self.constraint2_triple = []

        # Store the formulas in constraint4: consistency
        self.constraint4_formula1 = []
        self.constraint4_formula2 = []
        # Store the (tw1, tw2, reset) triple in which both tw1[:-1] == tw2[:-1] and tw1 == tw2
        self.constraint4_triple1 = []
        # Store the (tw1, tw2, reset) triple in which tw1[:-1] == tw2[-1]
        self.constraint4_triple2 = []
        # Store the (tw1, tw2, reset, f) triple in which records resets for tw1[:-1] == tw2[:-1]
        self.constraint4_triple3 = []

        self.addPath(())

        # Count the number of occurrence
        self.formulas_count = dict()

        # Store the query result
        self.query_result = dict()

    def __str__(self):
        res = 'R:\n'
        for twR, info in sorted(self.R.items()):
            res += str(twR) + ': ' + str(info)
        res += 'S:\n'
        for twS, info in sorted(self.S.items()):
            res += str(twS) + ': ' + str(info)
        res += 'E:\n'
        res += '\n'.join(','.join(str(tw) for tw in twE) for twE in self.E)
        return res

    def addRow(self, tws, res):
        """When adding a new row, complete the corresponding information.
        
        Compare the new row with previous rows, find if there are new formulas on
        constriant1, constraint2, and constraint4.

        """
        # Create two z3 variables: r_n is a boolean variable for whether
        # there is reset following tws. s_n is an integer variable for
        # the assignment of the current state.
        self.reset_name[tws] = z3.Bool("r_%d" % len(self.R))
        self.state_name[tws] = z3.Int("s_%d" % len(self.R))
        sequence = TestSequence(tws, res)

        # Compare the new row with each of the existing rows. For each
        # existing row that can be distinguished from the new row under some
        # resets, add the corresponding constraint1. Otherwise, record the
        # inability to distinguish to constraint1_triple.
        for row in self.R:
            possible_resets = generate_row_resets(row, tws)
            for reset in possible_resets:
                if self.findDistinguishingSuffix(self.R[row], sequence, reset) is not None:
                    f = z3.Implies(self.encodeReset(reset, self.reset_name),
                                   self.state_name[row] != self.state_name[tws])
                    self.constraint1_formula.append(f)
                else:
                    self.constraint1_triple.append((row, tws, reset))

        new_Es = []
        for row in self.R:
            # For each existing row whose last action equals the new row.
            if row != () and tws != () and row[-1].action == tws[-1].action:
                possible_resets = generate_row_resets_enhance(row, tws)
                for reset in possible_resets:
                    if self.findDistinguishingSuffix(self.R[row[:-1]], self.R[tws[:-1]], reset) is None:
                        time_val1 = self.R[row[:-1]].getTimeVal(reset)
                        time_val2 = self.R[tws[:-1]].getTimeVal(reset)
                        if isSameRegion(time_val1+row[-1].time, time_val2+tws[-1].time):
                            f = z3.Implies(self.state_name[row[:-1]] == self.state_name[tws[:-1]],
                                           z3.Not(self.encodeReset(reset, self.reset_name)))
                            # If reached the same time region, then the two states being the same
                            # implies the two resets must be the same. Add the corresponding formula
                            # to constraint2, and record the information in constraint2_triple.
                            if reset[row] != reset[tws]:
                                self.constraint2_formula.append(f)
                                self.constraint2_triple.append((row, tws, reset, f))
                                continue

                            suffix = self.findDistinguishingSuffix(self.R[row], sequence, reset)
                            # If row[:-1] and tws[:-1] are not distinguishable by the current suffixes,
                            # but row and tws are distinguishable, add new suffix to E. Also add the
                            # constraint excluding row[:-1] and tws[:-1] being the same state under the
                            # given reset.
                            if suffix is not None:
                                self.constraint4_formula1.append(f)
                                # May become different after adding some suffixes
                                self.constraint4_triple2.append((row, tws, reset, f))
                                suffix = (TimedWord(row[-1].action, min(row[-1].time, tws[-1].time)),) + suffix
                                new_Es.append(suffix)

                            # If row and tws are also not distinguishable, add a constraint saying
                            # if row[:-1] and tws[:-1] are mapped to the same state, then under the
                            # given reset row and tws are also mapped to the same reset.
                            else:
                                f2 = z3.Implies(z3.And(self.state_name[row[:-1]] == self.state_name[tws[:-1]],
                                                       self.encodeReset(reset, self.reset_name)),
                                                self.state_name[row] == self.state_name[tws])
                                self.constraint4_formula2.append(f2)
                                self.constraint4_triple3.append((row, tws, reset, f2))
                                self.constraint4_triple1.append((row, tws, reset))

        # Add the new timed word to R.
        self.R[tws] = TestSequence(tws, res)

        # Add each new suffix.
        for e in new_Es:
            self.addSuffix(e)

    def addSuffix(self, suffix):
        """When adding a suffix, we can check if some pairs of tws can be
        distinguished now, new formulas can be added in constraint1 or constraint4.

        Check if there are rows in R that can be distinguished from all existing
        rows in S, and if so add them to S.

        """
        if suffix in self.E:
            return

        # Add new formulas to constraint1.
        self.E.append(suffix)
        delete_items = []
        for tw1, tw2, reset in self.constraint1_triple:
            if self.findDistinguishingSuffix(self.R[tw1], self.R[tw2], reset, suffix) is not None:
                f = z3.Implies(self.encodeReset(reset, self.reset_name),
                               self.state_name[tw1] != self.state_name[tw2])
                self.constraint1_formula.append(f)
                delete_items.append((tw1, tw2, reset))

        for t in delete_items:
            self.constraint1_triple.remove(t)

        # Remove unnecessary formulas from constraint2.
        delete_items = []
        for tw1, tw2, reset, f in self.constraint2_triple:
            if self.findDistinguishingSuffix(self.R[tw1[:-1]], self.R[tw2[:-1]], reset, suffix) is not None:
                self.constraint2_formula.remove(f)
                delete_items.append((tw1, tw2, reset, f))
        
        for t in delete_items:
            self.constraint2_triple.remove(t)

        # Remove unnecessary formulas from constraint4_formula1.
        if not self.constraint4_triple2:
            return

        delete_items = []
        for tw1, tw2, reset, f in self.constraint4_triple2:
            if self.findDistinguishingSuffix(self.R[tw1[:-1]], self.R[tw2[:-1]], reset, suffix) is not None:
                self.constraint4_formula1.remove(f)
                delete_items.append((tw1, tw2, reset, f))

        for t in delete_items:
            self.constraint4_triple2.remove(t)

        # Re-test condition for adding to constraint4_formula1. Should add to new_Es?
        delete_items = []
        for tw1, tw2, reset in self.constraint4_triple1:
            if self.findDistinguishingSuffix(self.R[tw1[:-1]], self.R[tw2[:-1]], reset, suffix) is None:
                time_val1 = self.R[tw1[:-1]].getTimeVal(reset)
                time_val2 = self.R[tw2[:-1]].getTimeVal(reset)
                if isSameRegion(time_val1+tw1[-1].time, time_val2+tw2[-1].time):
                    s = self.findDistinguishingSuffix(self.R[tw1], self.R[tw2], reset, suffix)
                    if s is not None:
                        f = z3.Implies(self.state_name[tw1[:-1]] == self.state_name[tw2[:-1]],
                                       z3.Not(self.encodeReset(reset, self.reset_name)))
                        self.constraint4_formula1.append(f)                        
                        self.constraint4_triple2.append((tw1, tw2, reset, f))
                        delete_items.append((tw1, tw2, reset))

        for t in delete_items:
            self.constraint4_triple1.remove(t)

        # Remove unnecessary formulas from constraint4_formula2.
        delete_items = []
        for tw1, tw2, reset, f in self.constraint4_triple3:
            if self.findDistinguishingSuffix(self.R[tw1], self.R[tw2], reset, suffix) is not None:
                self.constraint4_formula2.remove(f)
                delete_items.append((tw1, tw2, reset, f))

        for t in delete_items:
            self.constraint4_triple3.remove(t)

        # Check if some state in R can be added to S. A state in R can be
        # added to S if it is different from all existing rows in S under
        # all possible resets.
        delete_items = []
        for tw1 in self.R:
            if tw1 in self.S:
                continue
            is_new_state = True
            for tw2 in list(self.S.keys())+delete_items:
                possible_resets = generate_row_resets(tw1, tw2)
                
                for reset in possible_resets:
                    if self.findDistinguishingSuffix(self.R[tw1], self.R[tw2], reset, suffix) is None:
                        is_new_state = False
                
                if not is_new_state:
                    break

            if is_new_state:
                delete_items.append(tw1)

        # Add state from R into S.
        for tws in delete_items:
            res = self.ota.runTimedWord(tws)
            if self.checkNewState(tws, res) and self.ota.runTimedWord(tws) != -1:
                self.addToS(tws)

    def addToS(self, tws):
        """Add a new row to S. This also requires adding the row followed by
        (act, 0) for each action a into R.
        
        """
        assert tws in self.R and tws not in self.S, \
                "addToS: tws should be in R and not in S"
        self.S[tws] = self.R[tws]

        if self.ota.runTimedWord(tws) != -1:
            for act in self.actions:
                cur_tws = tws + (TimedWord(act, 0),)
                if cur_tws not in self.R:
                    self.addPath(cur_tws)

    def addPossibleS(self, tws):
        """Check if tws can be added into S. If not, add
        tws + (act, 0) for each action into R.
        
        """
        res = self.ota.runTimedWord(tws)
        if self.checkNewState(tws, res):
            # Distinct from all states in S, directly add to S
            self.addToS(tws)
        else:
            # Otherwise, add to extra_S
            self.extra_S[tws] = self.R[tws]
            for act in self.actions:
                new_tws = tws + (TimedWord(act, 0),)
                new_res = self.ota.runTimedWord(new_tws)
                if new_tws not in self.R:
                    self.addRow(new_tws, new_res)

    def addPath(self, tws):
        """Add the given path tws (and its prefixes) to R.
        
        Starting from the head, it keeps adding longer prefixes until reaching
        the sink.

        """
        tws = tuple(tws)
        assert tws not in self.R, "Redundant R: %s" % str(tws)
        for i in range(len(tws)+1):
            cur_tws = tws[:i]
            cur_res = self.ota.runTimedWord(cur_tws)
            if cur_tws not in self.R:
                self.addRow(cur_tws, cur_res)            
                is_new_state = self.checkNewState(cur_tws, cur_res)

                if is_new_state and cur_tws not in self.S and cur_res != -1:
                    self.addToS(cur_tws)

            if cur_res == -1:
                break

    def checkNewState(self, tws, res, flag=False):
        """Check if tw is different from any other rows in S."""
        if tws in self.S:
            return False
        
        sequence = TestSequence(tws, res)
        for row in self.S:
            if flag and row == tws:
                continue
            if row != tws:
                resets = generate_row_resets(row, tws)
                for reset in resets:
                    if self.findDistinguishingSuffix(self.R[row], sequence, reset) is None:
                        return False
            
        return True

    def findDistinguishingSuffix(self, info1, info2, resets, E=None):
        """Check whether the two timed words are equivalent.
        
        If equivalent according to the current E, return None.

        Otherwise, return the distinguishing suffix (which works by shifting
        the first timed word to align the clock).

        """
        if info1.is_accept != info2.is_accept or info1.is_sink != info2.is_sink:
            return tuple()  # empty suffix is distinguishing

        time1 = info1.getTimeVal(resets)
        time2 = info2.getTimeVal(resets)

        if E is None:
            suffix = self.E
        else:
            suffix = [E]

        for twE in suffix:
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

    def differentStateUnderReset(self):
        """Constraint 1: if two rows can be distinguished under a reset, then they
        cannot be mapped to the same state.

        """
        return self.constraint1_formula

    def noForbiddenPair(self):
        """Constraint 2: for any tow rows R1 + (a, t1) and R2 + (a, t2), 
        if states[R1] = states[R2], and they are in the same time interval,
        then they should have same reset settings.

        """
        return self.constraint2_formula

    def checkConsistency(self):
        """Constraint 4: for any two rows R1 + (a, t1), R2 + (a, t2). If R1 and R2 are
        in the same states, and under the current reset settings these two rows are in
        the same time interval, then their states should also be same.
        
        """
        return self.constraint4_formula1 + self.constraint4_formula2

    def setSinkRowReset(self):
        """Constraint 5: All sink rows's resets are set to True."""
        formulas = []
        for r, info in self.R.items():
            if info.is_sink:
                formulas.append(self.reset_name[r] == True)

        return formulas

    def encodeSRow(self):
        """Each row in S should have a unique state."""
        formulas = []
        for i, s in enumerate(self.S):
            formulas.append(self.state_name[s] == (i + 1))

        return formulas

    def encodeStateNum(self, state_num):
        """The state name of each row must be between 1 and state_num, except the
        sink states, which must have state_num equal to state_num + 1.
        
        """
        formulas = []
        for row, s in self.state_name.items():
            if self.R[row].is_sink:
                formulas.append(s == state_num + 1)
            else:
                formulas.append(s >= 1)
                formulas.append(s <= state_num)

        return formulas

    def encodeExtraS(self, state_num):
        """The states in extra_S must cover all remaining state_num."""
        formulas = []
        for i in range(len(self.S)+1, state_num+1):
            formulas.append(z3.Or(*(self.state_name[row] == i for row in self.extra_S)))

        return formulas

    def findReset(self, state_num, enforce_extra):
        """Find a valid setting of resets and states.
        
        state_num - number of locations in the automata.
        enforce_extra - whether to enforce the condition that all rows have a
            representative in S or extra_S.
            
        Return a tuple (resets, states). 

        """
        constraint1 = self.differentStateUnderReset()
        constraint2 = self.noForbiddenPair()
        constraint4 = self.checkConsistency()
        constraint5 = self.setSinkRowReset()
        constraint7 = self.encodeSRow()

        assert state_num >= len(self.S)
        constraint6 = self.encodeStateNum(state_num)
        if enforce_extra:
            constraint8 = self.encodeExtraS(state_num)
        else:
            constraint8 = []
        s = z3.Solver()
        s.add(*(constraint1 + constraint2 + constraint4 + constraint5 + constraint6 + constraint7 + constraint8))

        if str(s.check()) == "unsat":
            # No assignment can be found for current S, extra_S, and state_num
            return None, None

        # An assignment is found, construct resets and states from the model.
        model = s.model()
        resets, states = dict(), dict()

        for row in self.R:
            states[row] = str(model[self.state_name[row]])
            resets[row] = bool(model[self.reset_name[row]])

        states["sink"] = str(state_num + 1)

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
                if len(trans) == 0: # invalid transition!
                    for tw, pos in states.items():
                        if pos == source:
                            return False, tw
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
        location_objs = set()
        for tw, loc in states.items():
            if tw == "sink":
                location_objs.add(Location(loc, False, False, True))
            else:
                # location_objs.add(Location(loc, (tw==()), self.R[tw].is_accept, self.R[tw].is_sink))
                location_objs.add(Location(loc, (loc=="1"), self.R[tw].is_accept, self.R[tw].is_sink))

        candidateOTA = OTA(
            name=self.ota.name + '_',
            sigma=self.actions,
            locations=location_objs,
            trans=otaTrans,
            init_state='1',
            accept_states=accepts,
            sink_name=states['sink'])

        return True, candidateOTA

def compute_max_time(candidate):
    def parse_time(t):
        return 0 if t == "+" else int(t)
    max_time = 0
    for tran in candidate.trans:
        max_time = max(max_time, 
                    parse_time(tran.constraint.min_value), 
                    parse_time(tran.constraint.max_value))
    return max_time

def learn_ota(ota, limit=30, verbose=True):
    """Overall learning loop.
    
    limit - maximum number of steps.
    verbose - whether to print debug information.

    """
    print("Start to learn ota %s.\n" % ota.name)
    learner = Learner(ota)
    assist_ota = buildAssistantOTA(ota)
    max_time_ota = compute_max_time(ota)
    state_num = 1

    for step in range(1, limit):
        print("Step", step)

        # If size of S has increased beyond state_num, adjust state_num to
        # that size.
        if state_num < len(learner.S):
            state_num = len(learner.S)
            print("Adjust state_num to len(S) = %s" % state_num)

        print("#S = %d, #extra_S = %d, state_num = %d" % (
            len(learner.S), len(learner.extra_S), state_num
        ))

        # First, try with current state_num and enforce the constraint
        # that all representatives are in extra_S.
        resets, states = learner.findReset(state_num, True)

        # If fails, try again without the constraint that all representatives
        # are in extra_S. Add any new representative to extra_S.
        if resets is None:
            resets, states = learner.findReset(state_num, False)

            # If still not found, must increase state_num.
            if resets is None:
                state_num += 1
                print("Increment state_num to %s." % state_num)
                continue

            # Otherwise, add new representatives to extra_S.
            has_reps = dict()
            for i in range(1, state_num+1):
                has_reps[i] = False
            for row in learner.S:
                has_reps[int(states[row])] = True
            for row in learner.extra_S:
                has_reps[int(states[row])] = True

            new_reps = []
            for row in learner.R:
                if int(states[row]) <= state_num and not has_reps[int(states[row])]:
                    has_reps[int(states[row])] = True
                    new_reps.append(row)
            assert len(new_reps) > 0

            for rep in new_reps:
                print("Add %s to extra_S." % str(rep))
                learner.addPossibleS(rep)
            continue

        if verbose:
            print(learner)

        if resets is None:
            # Should not arrive here
            raise AssertionError

        if verbose:
            print("resets and states:")
            for tws, v in resets.items():
                print("  %s: %s %s" % (",".join(str(tw) for tw in tws), v, states[tws]))

        f, candidate = learner.buildCandidateOTA(resets, states)
        if not f:
            raise AssertionError("buildCandidateOTA failed.")

        max_time_candidate = compute_max_time(candidate)
        max_time = max(max_time_ota, max_time_candidate)
        res, ctx = ota_equivalent(max_time, assist_ota, candidate)

        if not res and verbose:
            print(candidate)
        if res:
            print(candidate)
            print("Finished in %s steps " % step)
            # OTAToJSON(candidate, "candidate")
            # break
            return candidate

        ctx_path = tuple(ctx.find_path(assist_ota, candidate))
        if verbose:
            print("Counterexample", ctx_path, ota.runTimedWord(ctx_path), candidate.runTimedWord(ctx_path))
        learner.addPath(ctx_path)
