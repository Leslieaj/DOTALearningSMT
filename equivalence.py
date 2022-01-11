"""Inclusion and equivalence tests between two nondeterministic
one-clock timed automata.

"""

import copy
from decimal import Decimal

from ota import TimedWord
from interval import Interval, zero_point_region


def round_div_2(r):
    """r is of the form 0.xxxn. If n is even, return 0.xxx(n/2).
    If n = 1, return 0.xxxx5. If n is odd greater than 1, return
    0.xxx((n+1)/2).

    """
    if r == Decimal(1):
        return Decimal('0.5')

    s = str(r)
    num_digit = len(s) - 2
    res = r * (Decimal(10) ** num_digit)
    if res % 2 == 0 or res == 1:
        return (res / Decimal(2)) / (Decimal(10) ** num_digit)
    else:
        return ((res + 1) / Decimal(2)) / (Decimal(10) ** num_digit)

class Letter:
    """A letter consists of a location and a region constraint. It also
    specifies which side ('A' or 'B') the letter is on.
    
    """
    def __init__(self, side, location, region):
        self.side = side
        self.location = location
        if not isinstance(region, Interval):
            region = Interval(region)
        self.region = region

    def __eq__(self, other):
        return self.side == other.side and self.location == other.location and \
            self.region == other.region

    def __hash__(self):
        return hash(('LETTER', self.side, self.location, self.region))

    def __str__(self):
        return self.side + ':' + self.location + ',' + str(self.region)

    def __repr__(self):
        return "Letter(%s,%s,%s)" % (self.side, self.location, self.region)


class Letterword:
    """A letterword is a list of sets of letters.
    
    frac_times: list of fractional times.

    We also optionally keep track of how the letterword is arrived at,
    through the pre_lw and action parameters. They are not considered
    during comparison and hashing.

    pre_lw: previous letter word (None if not set).
    action: 'DELAY' or the name of an action.

    """
    def __init__(self, lst, frac_times, pre_lw=None, action=''):
        self.lst = list(lst)
        self.frac_times = [Decimal(v) for v in frac_times]
        self.pre_lw = pre_lw
        self.action = action

        assert len(self.lst) <= 2
        if len(self.lst) == 1:
            assert len(self.lst[0]) == 2, ("self.lst = %s" % self.lst)
        else:
            assert len(self.lst[0]) + len(self.lst[1]) == 2

    def __eq__(self, other):
        return self.lst == other.lst and self.frac_times == other.frac_times

    def __hash__(self):
        return hash(('LETTERWORD', self.lst, self.frac_times))

    def __str__(self):
        return str(self.lst) + ',' + str(self.frac_times)

    def __repr__(self):
        return str(self.lst) + ',' + str(self.frac_times)

    def is_all_inf(self):
        """Whether all letters in self have the infinite region."""
        for letter_set in self.lst:
            if not all(letter.region.is_inf_region() for letter in letter_set):
                return False
        return True

    def delay_one(self, max_time_value):
        """Delay for the minimal amount that changes the letterword.
        
        If the first set has a point region (and so must correspond to an integer),
        increment the first set. Otherwise, increment the last set to an integer
        and rotate it into the first position.

        """
        if any(fst.region.is_point_region() for fst in self.lst[0]):
            # First set is integer, shift first set to a small decimal.
            assert self.frac_times[0] == 0.0, 'delay_one: inconsistent time_dct'

            time_increment = round_div_2(Decimal(1) - self.frac_times[-1])
            new_frac_times = [v + time_increment for v in self.frac_times]
            
            fst_set = set()
            for fst in self.lst[0]:
                fst_set.add(Letter(fst.side, fst.location, fst.region.next_region(max_time_value)))
            return Letterword([fst_set] + self.lst[1:], new_frac_times), time_increment
        else:
            # Otherwise, shift the last set to an integer.
            time_increment = Decimal(1) - self.frac_times[-1]
            new_frac_times = [Decimal('0.0')]
            for i in range(len(self.lst)-1):
                new_frac_times.append(self.frac_times[i] + time_increment)

            fst_set = set()
            for fst in self.lst[-1]:
                fst_set.add(Letter(fst.side, fst.location, fst.region.next_region(max_time_value)))
            return Letterword([fst_set] + self.lst[:-1], new_frac_times), time_increment

    def delay_seq(self, max_time_value):
        """Find the sequence of delays starting from a letterword."""
        current_lw = self
        results = [Letterword(self.lst, self.frac_times, self, Decimal(0))]
        increment = Decimal(0)
        while not current_lw.is_all_inf():
            next_lw, next_increment = current_lw.delay_one(max_time_value)
            increment += next_increment
            next_lw.pre_lw = self
            next_lw.action = increment
            results.append(next_lw)
            current_lw = next_lw

        return results

    def can_dominate(self, lw2):
        """Determine whether self can dominate lw2 (lw2 <= self)."""
        id_self = 0
        id2 = 0
        for letter_set in self.lst:
            for i in range(id2, len(lw2.lst)):
                if letter_set.issubset(lw2.lst[i]):
                    id2 = i + 1
                    id_self += 1
                    break
        return id_self == len(self.lst)

    def is_bad(self, ota_A, ota_B):
        """Determine whether the letterword is bad. That is the B-side is
        accepting, but none of the A-side is accepting.

        """
        A_accept, B_accept = False, False
        for letter_set in self.lst:
            for letter in letter_set:
                if letter.side == 'A':
                    if letter.location in ota_A.accept_states:
                        A_accept = True
                if letter.side == 'B':
                    if letter.location in ota_B.accept_states:
                        B_accept = True

        return B_accept and not A_accept

    def immediate_asucc(self, ota_A, ota_B):
        """Perform an immediate action, without further time delays.

        ota_A : OTA, timed automata on the A side.
        ota_B : OTA, timed automata on the B side.

        """
        assert ota_A.sigma == ota_B.sigma, "immediate_asucc: OTAs must have the same actions."

        # List of all successors.
        all_res = []

        def make_lst(reset_list, noreset_list):
            """Construct new configuration from a list of Letters after reset
            (so must have region [0,0]), and a dictionary of list of Letters
            without reset.

            Returns the pair lst, frac_times for the new letterword.
            
            """
            new_lst = []
            new_frac_times = []

            if len(reset_list) > 0:
                # First, figure out whether the noreset_list contains a point region.
                has_point_region = any(letter.region.is_point_region() for letter in noreset_list[0])

                new_lst.append(set(reset_list))
                new_frac_times.append(Decimal(0))
                if has_point_region:
                    new_lst[0] = new_lst[0].union(noreset_list[0])
                elif noreset_list[0]:
                    new_lst.append(set(noreset_list[0]))
                    new_frac_times.append(self.frac_times[0])

                for i in range(1,len(self.lst)):
                    if noreset_list[i]:
                        new_lst.append(set(noreset_list[i]))
                        new_frac_times.append(self.frac_times[i])
            else:
                for i in range(len(self.lst)):
                    if noreset_list[i]:
                        new_lst.append(set(noreset_list[i]))
                        new_frac_times.append(self.frac_times[i])

            return new_lst, new_frac_times

        for action in ota_A.sigma:
            # Check all successors on the A and B side.
            # Successors is put into two lists.
            # reset_list are those letters that have time set to zero. Only
            # new location is recorded.
            # noreset_list are those letters whose time is unchanged. It is kept
            # as a dictionary mapping from place in original Letterword.
            A_reset_list, A_noreset_list = [], dict()
            B_reset_list, B_noreset_list = [], dict()

            for i in range(len(self.lst)):
                A_noreset_list[i] = []
                B_noreset_list[i] = []

            for i, letter_set in enumerate(self.lst):
                for letter in letter_set:
                    if letter.side == 'A':
                        for tran in ota_A.trans_dict[(action, letter.location)]:
                            if tran.constraint.contains_interval(letter.region):
                                if tran.reset:
                                    A_reset_list.append(Letter('A', tran.target, zero_point_region))
                                else:
                                    A_noreset_list[i].append(Letter('A', tran.target, letter.region))
                    else:  # letter.side == 'B'
                        for tran in ota_B.trans_dict[(action, letter.location)]:
                            if tran.constraint.contains_interval(letter.region):
                                if tran.reset:
                                    B_reset_list.append(Letter('B', tran.target, zero_point_region))
                                else:
                                    B_noreset_list[i].append(Letter('B', tran.target, letter.region))

            for B_reset in B_reset_list:
                reset_list = A_reset_list + [B_reset]
                noreset_list = A_noreset_list
                new_lst, new_frac_times = make_lst(reset_list, noreset_list)
                all_res.append(Letterword(new_lst, new_frac_times, self, action))

            for i, B_noresets in B_noreset_list.items():
                for B_noreset in B_noresets:
                    reset_list = A_reset_list
                    noreset_list = copy.deepcopy(A_noreset_list)
                    noreset_list[i].append(B_noreset)
                    new_lst, new_frac_times = make_lst(reset_list, noreset_list)
                    all_res.append(Letterword(new_lst, new_frac_times, self, action))

        return all_res

    def compute_wsucc(self, max_time_value, ota_A, ota_B):
        delay_seq = self.delay_seq(max_time_value)
        results = []
        for delay in delay_seq:
            imm_asucc = delay.immediate_asucc(ota_A, ota_B)
            for asucc in imm_asucc:
                if asucc not in results:
                    results.append(asucc)
        return results

    def find_path(self, ota_A, ota_B):
        """Returns the timed word reaching self."""
        current_lw = self
        tws = []
        init = init_letterword(ota_A, ota_B)
        while current_lw != init:
            assert isinstance(current_lw.action, str), 'find_path'
            action = current_lw.action
            current_lw = current_lw.pre_lw
            assert isinstance(current_lw.action, Decimal), 'find_path'
            time = current_lw.action
            tws.append(TimedWord(action, time))
            current_lw = current_lw.pre_lw

        return list(reversed(tws))


def init_letterword(ota_A, ota_B):
    """Returns the initial letterword for determining inclusion L(B) <= L(A)."""
    return Letterword([{Letter('A', ota_A.init_state, zero_point_region),
                        Letter('B', ota_B.init_state, zero_point_region)}], [0])

def explored_dominated(explored, w, ota_A, ota_B):
    # if both_reach_sink(w, ota_A, ota_B) == True:
    #     return True
    for v in explored:
        if v.can_dominate(w):
            return True
    return False

def both_reach_sink(lw, ota_A, ota_B):
    """Determine whether both letters in letterword lw have reached A's and B's sink location respectively.
        Now, we just consider deterministic OTA, so every lw just contains 2 letter, one is for A and the other is for B.
    """
    letter1 = None
    letter2 = None
    if len(lw.lst) == 1:
        # print(lw.lst)
        letter1, letter2 = list(lw.lst[0])
    if len(lw.lst) == 2:
        assert len(list(lw.lst[0])) == 1 and len(list(lw.lst[1])) == 1
        letter1 = list(lw.lst[0])[0]
        letter2 = list(lw.lst[1])[0]
    if letter1.side == 'A' and letter2.side == 'B': 
        if letter1.location == ota_A.sink_name and letter2.location == ota_B.sink_name:
            return True
        else:
            return False
    elif letter1.side == 'B' and letter2.side == 'A':
        if letter1.location == ota_B.sink_name and letter2.location == ota_A.sink_name:
            return True
        else:
            return False
    else:
        raise NotImplementedError("The format of letterword in function both_reach_sink")

def ota_inclusion(max_time_value, ota_A, ota_B):
    """Determines the inclusion L(B) <= L(A).
    
    Returns True, None if L(B) <= L(A). Otherwise, returns False, ctx,
    where ctx is a timed word accepted by B but not by A.

    """
    w0 = init_letterword(ota_A, ota_B)
    to_explore = [w0]
    explored = []
    while True:
        if len(to_explore) == 0:
            return True, None

        w = to_explore[0]
        del to_explore[0]
        if w.is_bad(ota_A, ota_B):
            return False, w  # return counterexample

        while explored_dominated(explored, w, ota_A, ota_B):
            if len(to_explore) == 0:
                return True, None
            w = to_explore[0]
            del to_explore[0]
            if w.is_bad(ota_A, ota_B):
                return False, w

        # if both_reach_sink(w, ota_A, ota_B) == True:
        #     #print("both reach sink")
        #     continue

        wsucc = w.compute_wsucc(max_time_value, ota_A, ota_B)
        for nw in wsucc:
            if nw not in to_explore:
            # if nw not in to_explore and both_reach_sink(nw, ota_A, ota_B) == False:
                to_explore.append(nw)
        if w not in explored:
            explored.append(w)

def ota_equivalent(max_time_value, ota_A, ota_B):
    incl_BA, ctx = ota_inclusion(max_time_value, ota_A, ota_B)
    if not incl_BA:
        return False, ctx
    
    incl_AB, ctx = ota_inclusion(max_time_value, ota_B, ota_A)
    if not incl_AB:
        return False, ctx

    return True, None
