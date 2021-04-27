from ota import Location, TimedWord, OTA, OTATran, buildAssistantOTA
from interval import Interval
from equivalence import ota_equivalent
import z3

"""
The guessed information maybe wrong in consistency checking, for example, 
tw1 + (a, 1.8) and tw1 + (a, 2.0) may in the same time region under resets 
but in fact not, it cannot be checked out if we only put (a, 1.8) into E.

"""


def isSameRegion(t1, t2):
    """Check whether t1 and t2 lies in the same region. That is,
    if they are equal, or if they are both non-integers in the same
    interval (n, n+1).

    """
    return t1 == t2 or (int(t1) != t1 and int(t2) != t2 and int(t1) == int(t2))

def isPrefix(tw1, tw2):
    """Determine whether tw1 is a prefix of tw2."""
    if len(tw1) > len(tw2):
        return False
    for i in range(len(tw1)):
        if tw1[i] != tw2[i]:
            return False

    return True

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
        # for tws, val in sorted(self.info.items()):
        #     res += '  %s: %s\n' % (','.join(str(tw) for tw in tws), val)
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

class SMTLearner:
    """Represents the state of a learner."""
    def __init__(self, ota):
        self.ota     = ota
        self.actions = ota.sigma

        # R contains test sequences which are used to distinguish states
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
        # res = "R:\n"
        # for twS, info in sorted(self.R.items()):
        #     res += str(twS) + ': ' + str(info)
        # res += "E:\n"
        # res += '\n'.join(','.join(str(tw) for tw in twE) for twE in self.E)
        # return res
        sink, non_sink = dict(), dict()
        for row, info in self.R.items():
            if info.is_sink:
                sink[row] = info
            else:
                non_sink[row] = info


        res = "R\\E:    %s\n" % ' '.join(str(e) for e in self.E) 
        for r in non_sink:
            e_res = " ".join(str(self.ota.runTimedWord(r + e)) for e in self.E)
            res += "%s: %s %s\n" % (r, self.ota.runTimedWord(r), e_res)

        return res

    def addPath(self, tws):
        """Add the given path tws (and its prefix) to R 
        as long as its prefix is not trapped in sink location.
        
        If tws does not go to sink, then additionally add tws + (a, 0) 
        for each action.
        """
        tws = tuple(tws)
        assert tws not in self.R,"addPath: tws should not be in R."
        tws = tuple(tws)
        for i in range(len(tws)+1):
            cur_tws = tws[:i]

            cur_res = self.ota.runTimedWord(cur_tws)
            if cur_tws not in self.R:
                self.R[cur_tws] = TestSequence(cur_tws, cur_res)
            if cur_res == -1:
                break
            for act in self.actions:
                cur_act = cur_tws + (TimedWord(act, 0),)
                if cur_act not in self.R:
                    cur_act_res = self.ota.runTimedWord(cur_act)
                    self.R[cur_act] = TestSequence(cur_act, cur_act_res)        

    def findDistinguishingSuffix(self, info1, info2, resets):
        """Check whether the two timed words are equivalent.
        
        If equivalent according to the current E, return None.

        Otherwise, return the distinguishing suffix (which works by shifting
        the first timed word to align the clock).

        """
        if self.R[info1].is_accept != self.R[info2].is_accept or self.R[info1].is_sink != self.R[info2].is_sink:
            return tuple()  # empty suffix is distinguishing

        time1 = self.R[info1].getTimeVal(resets)
        time2 = self.R[info2].getTimeVal(resets)

        for twE in self.E:
            if time1 == time2:
                res1 = self.R[info1].testSuffix(self.ota, twE)
                res2 = self.R[info2].testSuffix(self.ota, twE)
            elif time1 < time2:
                shift = time2 - time1
                res1 = self.R[info1].testSuffix(self.ota, twE, shift)
                res2 = self.R[info2].testSuffix(self.ota, twE)
            else:  # time1 > time2
                shift = time1 - time2
                res1 = self.R[info1].testSuffix(self.ota, twE)
                res2 = self.R[info2].testSuffix(self.ota, twE, shift)
        
            if res1 != res2:
                return twE

        return None


    def findAllPrefixRow(self, tw, non_sink):
        """Find all rows which take tw as their prefixes."""
        words = []
        for r in non_sink:
            if isPrefix(tw, r):
                words.append(r)

        return words

    def allResetVar(self, tws, resets):
        """Return all boolean variables related to tw."""
        tws = tuple(tws)
        return [resets[tws[:i]] for i in range(len(tws)+1)]

    def distinguishSamePrefix(self, row_resets, row_states, non_sink):
        """
        Return the formula which distinguish states in same prefix.

        If A and B have same prefixes and A's state is different from B, then
        A is different from B's which take B as their prefixes.
        """
        # the SMT formula
        formulas = []

        # map each row to non-reset
        non_reset = dict((row, False) for row in non_sink)

        # For each row_i, row_j, if row_i is a prefix of row_j, 
        # we need to check their behaviours under all resets is false,
        # if there exists a suffix e which distinguish row_i from row_j, 
        # we can construct a formula reset_information --> state(row_i) != state(row_j)
        for r_i in non_sink:
            for r_j in self.findAllPrefixRow(r_i, non_sink):
                if self.findDistinguishingSuffix(r_i, r_j, non_reset) is not None:
                    bool_vars = [row_resets[r_j[:i+1]] for i in range(len(r_j))]
                    i_state, j_state = row_states[r_i], row_states[r_j]
                    if len(bool_vars) == 1:
                        f = z3.Implies(z3.Not(bool_vars[0]), i_state != j_state)
                    else:
                        f = z3.Implies(z3.And(*[z3.Not(b) for b in bool_vars]), i_state != j_state)
                    formulas.append(f)

        # If there is no distinguihsing suffix for all rows, then we could assume that all resets are false
        if not formulas:
            for _, b in row_resets.items():
                formulas.append(z3.Not(b))

        return formulas

    def checkValidity(self, resets, states, R):
        """Return a formula guarantees that if two rows behave similarly under all states,
        then their states should be the same.
        """
        formula = []
        for r_i in R:
            for r_j in R:
                if self.findDistinguishingSuffix(r_i, r_j, resets) is None:
                    formula.append(states[r_j] == states[r_j])

        return formula

    def checkConsistent(self, resets):
        """Check whether the table is consistent.
        
        If not, the distinguishing tw should be added into E.
        """
        for r_i in self.R:
            for r_j in self.R:
                if r_i != () and r_j != () and r_i[-1].action == r_j[-1].action:
                    same_until_last_tw = self.findDistinguishingSuffix(r_i[:-1], r_j[:-1], resets)
                    if same_until_last_tw is None: # need to check 
                        time_val1 = self.R[r_i[:-1]].getTimeVal(resets)
                        time_val2 = self.R[r_j[:-1]].getTimeVal(resets)
                        if isSameRegion(r_i[-1].time+time_val1, r_j[-1].time+time_val2):
                            suffix = self.findDistinguishingSuffix(r_i, r_j, resets)
                            if suffix is None:
                                continue
                            # assert suffix is not None, 'No distinguishing suffix found.'
                            newE = (TimedWord(r_i[-1].action, min(r_i[-1].time, r_j[-1].time)),) + suffix
                            if newE in self.E:
                                print('resets', resets)
                                print('tw1', r_i)
                                print('tw2', r_j)
                                print('time1', time_val1)
                                print('time2', time_val2)
                                print('suffix', suffix)
                                print('newE', newE)
                                raise AssertionError('Repeated newE.')
                            return newE

        return None

    # def findReset(self):
    #     """Find a valid setting of resets.
        
    #     Returns a tuple (resets, foundR). If success, then resets is a dictionary 
    #     mapping from nonempty keys R to booleans.

    #     If fails, then resets is None.
        

    #     First check if the table is inconsistency and add corrsponding words into E. After the table is ready, 
    #     construct a formula and use z3 to find assignments for the states and resetting information. 
    #     """
    #     # Take a guess for each non-sink row in R.
    #     non_sink = dict((tw, info) for tw, info in self.R.items()
    #                 if not info.is_sink)

    #     sink = dict((tw, info) for tw, info in self.R.items()
    #                 if info.is_sink)

    #     num_guess = len(non_sink)

    #     z3_resets = z3.Bools(' '.join(['b_%s' % i for i in range(num_guess)]))
    #     z3_states = z3.Ints(' '.join(['s_%s' % i for i in range(num_guess)]))

    #     # map from row to reset information
    #     row_resets = dict((row, reset) for row, reset in zip(sorted(non_sink.keys()), z3_resets))
        
    #     # map from row to state
    #     row_states = dict((row, state) for row, state in zip(sorted(non_sink.keys()), z3_states))

    #     formulas = self.distinguishSamePrefix(row_resets, row_states, non_sink)

    #     # Limitation for the non-sink states value
    #     for tw, info in non_sink.items():
    #         formulas.append(z3.And(row_states[tw] >= 1, row_states[tw] <= num_guess))

    #     # The init state should be set to 0
    #     formulas.append(row_states[()] == 1)

    #     s = z3.Solver()
    #     for f in formulas:
    #         s.add(f)


    #     while True:
    #         assert s.check() == z3.sat, "The encoding of table is wrong."
    #         m = s.model()

    #         # z3 may not produce some variables's value

    #         # get reset information from model
    #         resets_model = dict((tw, True) for tw in sink)
    #         for r, b in row_resets.items():
    #             if m[b] is None:
    #                 resets_model[r] = False
    #             else:
    #                 resets_model[r] = bool(m[b])

    #         # check consistenty
    #         newE = self.checkConsistent(resets_model)
    #         if newE is not None:
    #             # if the table is not consistent, the newE should be added into 
    #             # E, and z3 needs to find a new assignment.
    #             self.E.append(newE)
                
    #             e_formulas = self.distinguishSamePrefix(row_resets, row_states, non_sink)

    #             s = z3.Solver()
    #             for f in e_formulas:
    #                 s.add(f)
    #                 s.add(row_states[()] == 1)

    #             for tw, info in non_sink.items():
    #                 s.add(z3.And(row_states[tw] >= 1, row_states[tw] <= num_guess))
                
    #             continue

    #         # If two rows r_a, r_b behave differently, assign their states different value. 
    #         for r_i in non_sink:
    #             for r_j in non_sink:
    #                 if self.findDistinguishingSuffix(r_i, r_j, resets_model) is not None:
    #                     s.add(row_states[r_i] != row_states[r_j])

    #         #
            
    #         # print("Solver: ", s)
    #         assert s.check() == z3.sat, "Encoding error."
    #         m = s.model()
    #         # print("model: ", m)
    #         break


    #     resets = dict((tw, True) for tw in sink)
    #     states = dict()

    #     for row, b in row_resets.items():
    #         if m[b] is not None:
    #             resets[row] = bool(m)
    #         else:
    #             resets[row] = False

    #     for row, state in row_states.items():
    #         if m[state] is not None:
    #             states[row] = str(m[state])
    #         else:
    #             raise ValueError
    
    #     return resets, states
    def findReset(self):
        # distinguish sink row and non-sink row
        sink, non_sink = dict(), dict()
        for row, info in self.R.items():
            if info.is_sink:
                sink[row] = info
            else:
                non_sink[row] = info

        num_guess = len(non_sink)

        # z3 variables
        row_resets = dict((row, z3.Bool("b_%s" % i)) for row, i in zip(sorted(non_sink), range(num_guess)))
        row_states = dict((row, z3.Int("s_%s" % i)) for row, i in zip(sorted(non_sink), range(num_guess)))

        while True:
            s = z3.Solver()
            
            # constraint the states' value in [1..len(non_sink)]
            for _, st in row_states.items():
                s.add(z3.And(st >= 1, st <= num_guess))

            # the initial states should be 1
            s.add(row_states[()] == 1)

            # the formulas which distinguish rows from all-non-reset information
            same_prefix_formula = self.distinguishSamePrefix(row_resets, row_states, non_sink)
            for f in same_prefix_formula:
                s.add(f)

            # assert s.check() == z3.sat, "Invalid R."
            # translation(z3's model may not contain all variables)

            while True: # check invalid pairs
                assert s.check() == z3.sat, "Invalid R."
                m = s.model()
                resets_model = self.encoding_resets(m, row_resets, sink)
                if not self.checkForbiddenPairs(resets_model):
                    bool_val = []
                    for var, val in resets_model.items():
                        if var in sink:
                            continue
                        if val:
                            bool_val.append(row_resets[var])
                        else:
                            bool_val.append(z3.Not(row_resets[var]))
                    if len(bool_val) == 1:
                        s.add(z3.Not(bool_val[0]))
                    else:
                        s.add(z3.Not(z3.And(*bool_val)))
                else:
                    assert s.check() == z3.sat, "Invalid R."
                    m = s.model()
                    break



            
            while True: # check invalid rows
                m = s.model()

                resets_model = self.encoding_resets(m, row_resets, sink)

                # check the reset encoding whether makes some rows invalid which means 
                # that, in the actual automata, two rows in R representr different states 
                # but under the current reset encoding, they are in the same time region.
                if not self.checkInvalidRow(resets_model):
                    bool_val = []
                    for var, val in resets_model.items():
                        if var in sink:
                            continue
                        if val:
                            bool_val.append(row_resets[var])
                        else:
                            bool_val.append(z3.Not(row_resets[var]))
                    # bool_val = [row_resets[v] for v, _ in resets_model.items() if v in non_sink]
                    if len(bool_val) == 1:
                        s.add(z3.Not(bool_val[0]))
                    else:
                        s.add(z3.Not(z3.And(*bool_val)))
                else:
                    assert s.check() == z3.sat, "Invalid R."
                    m = s.model()
                    break


            resets_model = self.encoding_resets(m, row_resets, sink)            
            # check inconsistency
            newE = self.checkConsistent(resets_model)
            if newE is not None:
                self.E.append(newE)
                continue

            # if two rows tw1, tw2 are equal, then for all rows tw1 * a, tw2 * a,
            # they have same states

            for tw1 in non_sink:
                for tw2 in non_sink:
                    if tw1 == tw2 or tw1 == () or tw2 == (): # trivial
                        continue

                    if self.findDistinguishingSuffix(tw1[:-1], tw2[:-1], resets_model) is None\
                        and tw1[-1].action == tw2[-1].action:
                        time_val1 = self.R[tw1[:-1]].getTimeVal(resets_model)
                        time_val2 = self.R[tw2[:-1]].getTimeVal(resets_model)
                        if isSameRegion(time_val1+tw1[-1].time, time_val2+tw2[-1].time):
                            assert self.findDistinguishingSuffix(tw1, tw2, resets_model) is None, "Inconsistency."
                            s.add(row_states[tw1] == row_states[tw2])

                    suffix = self.findDistinguishingSuffix(tw1, tw2, resets_model)
                    if suffix is not None:
                        s.add(row_states[tw1] != row_states[tw2])
                    else:
                        s.add(row_states[tw1] == row_states[tw2])
            
            assert s.check() == z3.sat, "Invalid R."
            m = s.model()
            break

        

        resets = dict((tw, True) for tw in sink)
        states = dict()

        for row, b in row_resets.items():
            if m[b] is not None:
                resets[row] = bool(m)
            else:
                resets[row] = False

        for row, state in row_states.items():
            if m[state] is not None:
                states[row] = str(m[state])
            else:
                raise ValueError
    
        return resets, states

    def encoding_resets(self, model, row_resets, sink):
        resets_model = dict((tw, True) for tw in sink)
        for r, b in row_resets.items():
            if model[b] is None:
                resets_model[r] = False
            else:
                resets_model[r] = bool(model[b])

        return resets_model
            
    def checkInvalidRow(self, resets):
        """Check whether there are invalid rows.

        An invalid row is given by the fact that it can be distinguished from
        itself under the given resets.
        """
        for tw1 in self.R:
            for tw2 in self.R:
                if tw1 != () and tw2 != () and tw1[:-1] == tw2[:-1] \
                  and tw1[-1].action == tw2[-1].action and \
                    self.ota.runTimedWord(tw1) != self.ota.runTimedWord(tw2):
                    time_val1 = self.R[tw1[:-1]].getTimeVal(resets)
                    time_val2 = self.R[tw2[:-1]].getTimeVal(resets)


                    if isSameRegion(time_val1+tw1[-1].time, time_val2+tw2[-1].time):
                        return False

        return True

    # def checkForbiddenPairs(self, resets):
    #     """Check validity of reset information.

    #     The main check is that: for any R1 + (a, t1) and R2 + (a, t2),
    #     if foundR[R1] == foundR[R2], and the actions and times are the same,
    #     then the reset information should be the same.

    #     Returns whether the reset information is valid according to the above
    #     criteria.
    #     """
    #     for tw1 in self.R:
    #         for tw2 in self.R:
    #             if tw1 != () and tw2 != () and resets[tw1] != resets[tw2] and \
    #                 self.findDistinguishingSuffix(tw1[:-1], tw2[:-1], resets) is None:
    #                 time_val1 = self.R[tw1[:-1]].getTimeVal(resets)
    #                 time_val2 = self.R[tw2[:-1]].getTimeVal(resets)
    #                 if isSameRegion(time_val1, time_val2):
    #                     return False

    #     return True

    def checkSuffix(self, tw1, tw2):
        """To see if two timed words behave similarly in all suffix."""
        suffix = [()] + self.E
        
        for suf in suffix:
            if self.ota.runTimedWord(tw1+suf) != self.ota.runTimedWord(tw2+suf):
                return False

            return True


    def checkForbiddenPairs(self, resets):
        """
        For any two rows r_i, r_j, if they behave similarly at all suffix, then they 
        should not have distinguishing suffix.
        """
        for tw1 in self.R:
            for tw2 in self.R:
                if tw1 != () and tw2 != () and resets[tw1] != resets[tw2] and tw1[-1].action \
                  == tw2[-1].action and self.findDistinguishingSuffix(tw1[:-1], tw2[:-2], resets) is None:
                    time_val1 = self.R[tw1[:-1]].getTimeVal(resets)
                    time_val2 = self.R[tw2[:-1]].getTimeVal(resets)
                    if isSameRegion(time_val1+tw1[-1].time, time_val2+tw2[-1].time):
                        return False
                  
        return True

    
    def buildCandidateOTA(self, resets, foundR):
        """Construct candidate OTA from current information
        
        resets - guessed reset information for each entry in S and R.
        foundR - mapping from rows in S and R to rows in S (or the sink).
        
        """
        # the number of states
        state_set = set()
        for _, st in foundR.items():
            state_set.add(st)

        state_num = len(state_set)

        # Mapping from timed words to location names.
        # Each path in R should correspond to a location.
        locations = dict()

        locations['sink'] = str(state_num+1)

        for tw in self.R:
            if not self.R[tw].is_sink:
                locations[tw] = foundR[tw]
            else:
                locations[tw] = locations['sink']
        
        # Mapping from location, action and time to transitions,
        # in the form of (reset, target).
        transitions = dict()
        for i in range(state_num+1):
            name = str(i+1)
            transitions[name] = dict()
            for act in self.actions:
                transitions[name][act] = dict()

        # List of accept states
        accepts = []
        for tw in locations:
            if tw != 'sink' and self.R[tw].is_accept:
                accepts.append(locations[tw])
        
        # Fill in transitions using prefix in R. For each nonempty entry
        # in R, find its immediate predecessor.
        for tw in sorted(self.R):
            if tw == ():
                continue
            # print("tw: ", tw)
            # reset_info = ""
            # for i in range(len(tw)):
            #     if resets[tw[:i+1]]:
            #         reset_info += " ⊤"
            #     elif not resets[tw[:i+1]]:
            #         reset_info += " ⊥"
            # print("reset: ", reset_info)
            cur_loc = locations[tw]
            assert tw[:-1] in locations, 'R is not prefix closed'
            prev_loc = locations[tw[:-1]]
            start_time = self.R[tw[:-1]].getTimeVal(resets)
            trans_time = start_time + tw[-1].time
            if self.R[tw].is_sink:
                cur_reset, cur_loc = True, locations['sink']
            else:
                cur_reset, cur_loc = resets[tw], locations[tw]
            if trans_time in transitions[prev_loc][tw[-1].action] and \
                (cur_reset, cur_loc) != transitions[prev_loc][tw[-1].action][trans_time]:
                print('When adding transition for', tw)
                raise AssertionError('Conflict at %s %s %s' % (prev_loc, tw[-1].action, trans_time))
            transitions[prev_loc][tw[-1].action][trans_time] = cur_reset, cur_loc
            # print(transitions)

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
                location_objs.append(Location(loc, (tw == ()), self.R[tw].is_accept, self.R[tw].is_sink))

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
    learner = SMTLearner(ota)
    assist_ota = buildAssistantOTA(ota)
    for i in range(1, limit):
        print ('Step', i)
        resets, foundR = learner.findReset()

        if verbose:
            print(learner)

            # Found possible choice of resets.
            print('resets:')
            for tws, v in resets.items():
                print('  %s: %s' % (','.join(str(tw) for tw in tws), v))
            print('foundR:')
            for tws, state in foundR.items():
                print('  %s: %s' % (','.join(str(tw) for tw in tws), state))
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