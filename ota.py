# Nondeterministic one-clock timed automata

import json

from interval import Interval, complement_intervals


class Location:
    """A location in timed automata."""

    def __init__(self, name, init=False, accept=False, sink=False):
        self.name = name
        self.init = init
        self.accept = accept
        self.sink = sink

    def __str__(self):
        return self.name + ',' + str(self.init) + ',' + str(self.accept) + ',' + str(self.sink)


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

    def __init__(self, source, action, constraint, reset, target):
        """The initial data include:

        source : str, name of the source location.
        action : str, name of the action.
        constraint : Interval, constraint of the transition.
        reset : bool, whether the transition resets the clock.
        target : str, name of the target location.

        """
        self.source = source
        self.action = action
        self.constraint = constraint
        self.reset = reset
        self.target = target

    def is_pass(self, tw):
        """Whether tw is allowed by the transition.

        tw : TimedWord, input timed word.

        """
        return tw.action == self.action and self.constraint.contains_point(tw.time)


class OTA:
    """Represents a nondeterministic one-clock timed automata."""

    def __init__(self, name, sigma, locations, trans, init_state, accept_states):
        """The initial data are:

        name : str, name of the automata.
        sigma : list(str), list of actions.
        locations : list(Location), list of locations.
        trans : list(OTATran), list of transitions.
        init_state : str, name of the initial state.
        accept_states: list(str), list of accepting states.

        """
        self.name = name
        self.sigma = sigma
        self.locations = locations
        self.trans = trans
        self.init_state = init_state
        self.accept_states = accept_states
        self.sink_name = None

    def __str__(self):
        res = ""
        
        res += "OTA name: \n"
        res += self.name + "\n"
        res += "sigma and length of sigma: " + "\n"
        res += str(self.sigma) + " " + str(len(self.sigma)) + "\n"
        res += "Location (name, init, accept, sink) :\n"
        for l in self.locations:
            res += str(l) + "\n"
        res += "transitions (id, source_state, label, target_state, constraints, reset):\n"
        for t in self.trans:
            res += "%s %s %s %s %s\n" % (t.source, t.action, t.target, t.constraint, t.reset)
        res += "init state:\n"
        res += str(self.init_state) + "\n"
        res += "accept states:\n"
        res += str(self.accept_states) + "\n"
        res += "sink states:\n"
        res += str(self.sink_name) + "\n"
        return res


def buildOTA(jsonfile):
    """Build the teacher OTA from a json file."""
    with open(jsonfile, 'r') as f:
        data = json.load(f)
        name = data["name"]
        locations_list = [l for l in data["l"]]
        sigma = [s for s in data["sigma"]]
        trans_set = data["tran"]
        init_state = data["init"]
        accept_list = [l for l in data["accept"]]
        L = [Location(location, False, False) for location in locations_list]
        for l in L:
            if l.name == init_state:
                l.init = True
            if l.name in accept_list:
                l.accept = True
        trans = []
        for tran in trans_set:
            source = trans_set[tran][0]
            label = trans_set[tran][1]
            constraint = Interval(trans_set[tran][2])
            reset = (trans_set[tran][3] == 'r')
            target = trans_set[tran][4]
            ota_tran = OTATran(source, label, constraint, reset, target)
            trans.append(ota_tran)
        return OTA(name, sigma, L, trans, init_state, accept_list)


def buildAssistantOTA(ota):
    """Build an assistant OTA which has the partitions at every node.
    The acceptance language is equal to teacher.

    """
    location_number = len(ota.locations)
    tran_number = len(ota.trans)
    sink = Location(str(location_number+1), False, False, True)

    new_trans = []
    for l in ota.locations:
        # Mapping from action to list of transitions from l with the action.
        l_dict = {}
        for key in ota.sigma:
            l_dict[key] = []

        for tran in ota.trans:
            if tran.source == l.name:
                l_dict[tran.action].append(tran.constraint)

        for key in l_dict:
            cuintervals = []
            if len(l_dict[key]) > 0:
                cuintervals = complement_intervals(l_dict[key])
            else:
                cuintervals = [Interval("[0,+)")]
            if len(cuintervals) > 0:
                for c in cuintervals:
                    new_trans.append(OTATran(l.name, key, c, True, sink.name))

    assist_name = "Assist_" + ota.name
    assist_locations = [location for location in ota.locations]
    assist_trans = [tran for tran in ota.trans]
    assist_init = ota.init_state
    assist_accepts = [sn for sn in ota.accept_states]
    if len(new_trans) > 0:
        # Add sink location
        assist_locations.append(sink)

        # Add transitions from normal locations to sink
        assist_trans.extend(new_trans)

        # Add loops from sink to sink
        for label in ota.sigma:
            assist_trans.append(OTATran(sink.name, label, Interval("[0,+)"), True, sink.name))

    assist_ota = OTA(assist_name, ota.sigma, assist_locations, assist_trans, assist_init, assist_accepts)
    assist_ota.sink_name = sink.name
    return assist_ota
