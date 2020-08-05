# Intervals and regions

class Interval:
    """Intervals can be used to represent constraints in a timed automata.

    An interval is specified by a left boundary and right boundary. Each
    boundary is either open or closed. The right boundary may be infinity
    (indicated by '+' and must be open).

    A union of intervals can be used to specify a subset of real numbers
    (generalized constraint).

    """
    def __init__(self, *args):
        """Constraints an interval from string input."""
        self.min_value = None
        self.max_value = None
        self.closed_min = None
        self.closed_max = None

        if len(args) == 1:
            s, = args  # Input is a string to be parsed

            try:
                min_type, max_type = s.split(',')
            except AttributeError:
                assert False, 'Unable to parse interval ' + str(s)

            if min_type[0] == '[':
                self.closed_min = True
            elif min_type[0] == '(':
                self.closed_min = False
            else:
                assert False, 'Unable to parse interval ' + s

            if max_type[-1] == ']':
                self.closed_max = True
            elif max_type[-1] == ')':
                self.closed_max = False
            else:
                assert False, 'Unable to parse interval ' + s

            try:
                self.min_value = int(min_type[1:])
                if max_type[:-1] == '+':
                    self.max_value = '+'
                    assert self.closed_max == False, 'Interval: right boundary cannot be +]'
                else:
                    self.max_value = int(max_type[:-1])
            except ValueError:
                assert False, 'Unable to parse interval ' + s

        elif len(args) == 4:
            # Argument is a 4-tuple.
            self.min_value, self.closed_min, self.max_value, self.closed_max = args
            assert type(self.min_value) == int and \
                (type(self.max_value) == int or (self.max_value == '+' and self.closed_max == False))

        else:
            raise NotImplementedError

    def __eq__(self, other):
        return self.min_value == other.min_value and self.max_value == other.max_value and \
            self.closed_min == other.closed_min and self.closed_max == other.closed_max

    def __hash__(self):
        return hash(('INTERVAL', self.min_value, self.closed_min, self.max_value, self.closed_max))

    def __str__(self):
        left = '[' if self.closed_min else '('
        right = ']' if self.closed_max else ')'
        return left + str(self.min_value) + ',' + str(self.max_value) + right

    def __repr__(self):
        return str(self)

    def contains_point(self, t):
        """Whether the given time is in the interval.

        t : Decimal, input time.

        """
        if self.closed_min:
            left_ok = (t >= self.min_value)
        else:
            left_ok = (t > self.min_value)
        if self.max_value == '+':
            right_ok = True
        elif self.closed_max:
            right_ok = (t <= self.max_value)
        else:
            right_ok = (t < self.max_value)
        return left_ok and right_ok

    def contains_interval(self, other):
        """Whether the interval contains another interval.

        other : Interval, input interval.

        """
        if self.closed_min or not other.closed_min:
            left_ok = (other.min_value >= self.min_value)
        else:
            left_ok = (other.min_value > self.min_value)
        if self.max_value == '+':
            right_ok = True
        elif other.max_value == '+':
            right_ok = False
        elif self.closed_max or not other.closed_max:
            right_ok = (other.max_value <= self.max_value)
        else:
            right_ok = (other.max_value < self.max_value)
        return left_ok and right_ok

    def is_point_region(self):
        """Whether the interval is of the form [t, t]."""
        return self.min_value == self.max_value and self.closed_min and self.closed_max

    def is_frac_region(self):
        """Whether the interval is of the form (t, t+1)."""
        return self.max_value == self.min_value + 1 and \
            self.closed_min == False and self.closed_max == False

    def is_inf_region(self):
        """Whether the interval is of the form (t, +),"""
        return self.max_value == '+' and self.closed_min == False and self.closed_max == False

    def next_region(self, max_time_value):
        """Return the region immediately after self."""
        if self.is_point_region():
            if self.min_value == max_time_value:
                return inf_region(self.min_value)
            else:
                return frac_region(self.min_value)
        elif self.is_frac_region():
            return point_region(self.max_value)
        elif self.is_inf_region():
            return inf_region(self.min_value)
        else:
            assert False, 'next_region'


def point_region(t):
    """Return the region [t, t]."""
    return Interval(t, True, t, True)

def frac_region(t):
    """Return the region (t, t+1)."""
    return Interval(t, False, t+1, False)

def inf_region(t):
    """Return the region (t, +)."""
    return Interval(t, False, '+', False)

def intervals_partition(intervals):
    """Compute the partition of the real numbers generated by the intervals."""

    # key_bns maintains a list of important left boundaries, as pairs
    # of (i, is_open). Note we use is_open so that closed left boundary
    # (with is_open = False) comes before open left boundary (with is_open = True)
    # at the same point. 
    key_bns = set()
    key_bns.add((0, False))
    for interval in intervals:
        key_bns.add((interval.min_value, not interval.closed_min))
        if interval.max_value != '+':
            key_bns.add((interval.max_value, interval.closed_max))
    
    key_bns = sorted(list(key_bns))
    partition = []
    for i in range(len(key_bns)-1):
        val1, is_open1 = key_bns[i]
        val2, is_open2 = key_bns[i+1]
        partition.append(Interval(val1, not is_open1, val2, is_open2))
    
    val_last, is_open_last = key_bns[-1]
    partition.append(Interval(val_last, not is_open_last, '+', False))
    return partition

def complement_intervals(intervals):
    partition = intervals_partition(intervals)

    complement_intvs = []
    for intv in partition:
        if all(not intv2.contains_interval(intv) for intv2 in intervals):
            if len(complement_intvs) > 0:
                last_intv = complement_intvs[-1]
                if last_intv.max_value == intv.min_value and last_intv.closed_max != intv.closed_min:
                    # Can connect the two intervals
                    complement_intvs[-1] = Interval(last_intv.min_value, last_intv.closed_min,
                                                    intv.max_value, intv.closed_max)
                else:
                    complement_intvs.append(intv)
            else:
                complement_intvs.append(intv)

    return complement_intvs
