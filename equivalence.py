"""Inclusion and equivalence tests between two nondeterministic
one-clock timed automata.

"""

import copy

from interval import Interval, point_region


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
    
    We also optionally keep track of how the letterword is arrived at,
    through the pre_lw and action parameters. They are not considered
    during comparison and hashing.

    pre_lw: previous letter word (None if not set).
    action: 'DELAY' or the name of an action.

    """
    def __init__(self, lst, pre_lw=None, action='DELAY'):
        self.lst = list(lst)
        self.pre_lw = pre_lw
        self.action = action

    def __eq__(self, other):
        return self.lst == other.lst

    def __hash__(self):
        return hash(('LETTERWORD', self.lst))

    def __str__(self):
        return str(self.lst)

    def __repr__(self):
        return str(self.lst)

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
            fst_set = set()
            for fst in self.lst[0]:
                fst_set.add(Letter(fst.side, fst.location, fst.region.next_region(max_time_value)))
            return Letterword([fst_set] + self.lst[1:])
        else:
            fst_set = set()
            for fst in self.lst[-1]:
                fst_set.add(Letter(fst.side, fst.location, fst.region.next_region(max_time_value)))
            return Letterword([fst_set] + self.lst[:-1])

    def delay_seq(self, max_time_value):
        """Find the sequence of delays starting from a letterword."""
        current_lw = self
        results = []
        while not current_lw.is_all_inf():
            next_lw = current_lw.delay_one(max_time_value)
            results.append(next_lw)
            current_lw = next_lw

        return results

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
            
            """
            new_lst = []

            if len(reset_list) > 0:
                # First, figure out whether the noreset_list contains a point region.
                has_point_region = any(letter.region.is_point_region() for letter in noreset_list[0])

                new_lst.append(set(reset_list))
                if has_point_region:
                    new_lst[0].union(noreset_list[0])
                elif noreset_list[0]:
                    new_lst.append(set(noreset_list[0]))

                for i in range(1,len(self.lst)):
                    if noreset_list[i]:
                        new_lst.append(set(noreset_list[i]))
            else:
                for i in range(len(self.lst)):
                    if noreset_list[i]:
                        new_lst.append(set(noreset_list[i]))

            return new_lst

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
                        for tran in ota_A.trans:
                            if tran.action == action and tran.source == letter.location and \
                                tran.constraint.contains_interval(letter.region):
                                if tran.reset:
                                    A_reset_list.append(Letter('A', tran.target, point_region(0)))
                                else:
                                    A_noreset_list[i].append(Letter('A', tran.target, letter.region))
                    else:  # letter.side == 'B'
                        for tran in ota_B.trans:
                            if tran.action == action and tran.source == letter.location and \
                                tran.constraint.contains_interval(letter.region):
                                if tran.reset:
                                    B_reset_list.append(Letter('B', tran.target, point_region(0)))
                                else:
                                    B_noreset_list[i].append(Letter('B', tran.target, letter.region))

            for B_reset in B_reset_list:
                reset_list = A_reset_list + [B_reset]
                noreset_list = A_noreset_list
                all_res.append(Letterword(make_lst(reset_list, noreset_list), self, action))

            for i, B_noresets in B_noreset_list.items():
                for B_noreset in B_noresets:
                    reset_list = A_reset_list
                    noreset_list = copy.deepcopy(A_noreset_list)
                    noreset_list[i].append(B_noreset)
                    all_res.append(Letterword(make_lst(reset_list, noreset_list), self, action))

        return all_res


def init_letterword(ota_A, ota_B):
    return Letterword([{Letter('A', ota_A.init_state, point_region(0)),
                        Letter('B', ota_B.init_state, point_region(0))}])
