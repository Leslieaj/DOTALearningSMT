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
