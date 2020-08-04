# Nondeterministic one-clock timed automata

class Location:
    """A location in timed automata."""

    def __init__(self, name, init=False, accept=False, sink=False):
        self.name = name
        self.init = init
        self.accept = accept
        self.sink = sink
