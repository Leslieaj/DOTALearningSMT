"""Inclusion and equivalence tests between two nondeterministic
one-clock timed automata.

"""

from interval import Interval


class Letter:
    """A letter consists of a location and a region constraint. It also
    specifies which side ('A' or 'B') the letter is on.
    
    """
    def __init__(self, side, location, constraint):
        self.side = side
        self.location = location
        if not isinstance(constraint, Interval):
            constraint = Interval(constraint)
        self.constraint = constraint

    def __eq__(self, other):
        return self.side == other.side and self.location == other.location and \
            self.constraint == other.constraint

    def __hash__(self):
        return hash(('LETTER', self.side, self.location, self.constraint))

    def __str__(self):
        return self.side + ':' + self.location + ',' + str(self.constraint)

    def __repr__(self):
        return "Letter(%s,%s,%s)" % (self.side, self.location, self.constraint)


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
        """Whether all letters in self have the infinite constraint."""
        for letter_set in self.lst:
            if not all(letter.constraint.is_inf_region() for letter in letter_set):
                return False
        return True

    def delay_one(self, max_time_value):
        """Delay for the minimal amount that changes the letterword.
        
        If the first set has a point region (and so must correspond to an integer),
        increment the first set. Otherwise, increment the last set to an integer
        and rotate it into the first position.

        """
        if any(fst.constraint.is_point_region() for fst in self.lst[0]):
            fst_set = set()
            for fst in self.lst[0]:
                fst_set.add(Letter(fst.side, fst.location, fst.constraint.next_region(max_time_value)))
            return Letterword([fst_set] + self.lst[1:])
        else:
            fst_set = set()
            for fst in self.lst[-1]:
                fst_set.add(Letter(fst.side, fst.location, fst.constraint.next_region(max_time_value)))
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

    def transition(self, A_trans, B_tran):
        """Perform the given set of transitions.

        A_trans : set(OTATran), set of non-deterministic choices on the A side.
        B_tran: OTATran, one transition on the B side.

        """
        pass
