# Nondeterministic one-clock timed automata

class Location:
    """A location in timed automata."""

    def __init__(self, name, init=False, accept=False, sink=False):
        self.name = name
        self.init = init
        self.accept = accept
        self.sink = sink


class TimedWord:
    """Timed word without reset information."""

    def __init__(self, action, time):
        """The initial data include:

        action : str, name of the action.
        time : Decimal, logical clock value.

        """
        self.action = action
        self.time = time

    def __eq__(self, other):
        return self.action == other.action and self.time == other.time

    def __hash__(self):
        return hash(('TIMEDWORD', self.action, self.time))

    def __str__(self):
        return '(%s,%s)' % (self.action, str(self.time))


class OTATran:
    """Represents a transition in timed automata."""

    def __init__(self, source, label, constraint, reset, target):
        """The initial data include:

        source : str, name of the source location.
        label : str, name of the action.
        constraint : Interval, constraint of the transition.
        reset : bool, whether the transition resets the clock.
        target : str, name of the target location.

        """
        self.source = source
        self.label = label
        self.constraint = constraint
        self.reset = reset
        self.target = target

    def is_pass(self, tw):
        """Whether tw is allowed by the transition.

        tw : TimedWord, input timed word.

        """
        return tw.action == self.label and self.constraint.contains_point(tw.time)
