# Nondeterministic one-clock timed automata

import json
from graphviz import Digraph
from interval import Interval, complement_intervals


class Location:
    """A location in timed automata."""

    def __init__(self, name, init=False, accept=False, sink=False):
        self.name = name
        self.init = init
        self.accept = accept
        self.sink = sink

    def __str__(self):
        return self.name

    def __repr__(self):
        return self.name

    def __eq__(self, other):
        return self.name == other.name and self.init == other.init and \
            self.accept == other.accept and self.sink == other.sink

    def __hash__(self):
        return hash((self.name, self.init, self.accept, self.sink))

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

    def __le__(self, other):
        return (self.action, self.time) <= (other.action, other.time)

    def __lt__(self, other):
        return (self.action, self.time) < (other.action, other.time)

    def __hash__(self):
        return hash(('TIMEDWORD', self.action, self.time))

    def __str__(self):
        return '(%s,%s)' % (self.action, str(self.time))

    def __repr__(self):
        return str(self)


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

    def __str__(self):
        return '%s %s %s %s %s' % (self.source, self.action, self.target, self.constraint, self.reset)

    def __repr__(self):
        return str(self)

    def is_pass(self, source, action, time):
        """Whether the given action and time is allowed by the transition.

        source : str, source of the action.
        action : str, name of the action.
        time : Decimal, time at which the action should occur.

        """
        return source == self.source and action == self.action and \
            self.constraint.contains_point(time)


class OTA:
    """Represents a nondeterministic one-clock timed automata."""

    def __init__(self, name, sigma, locations, trans, init_state, accept_states, sink_name=None):
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
        self.sink_name = sink_name

        # Create index of transitions
        self.trans_dict = dict()
        for action in self.sigma:
            for loc in self.locations:
                self.trans_dict[(action, loc.name)] = []

        for tran in self.trans:
            self.trans_dict[(tran.action, tran.source)].append(tran)

        # store the runTimedWord result
        self.query = dict()

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
            # if t.target != self.sink_name:
            res += "%s %s %s %s %s\n" % (t.source, t.action, t.target, t.constraint, t.reset)
        res += "init state:\n"
        res += str(self.init_state) + "\n"
        res += "accept states:\n"
        res += str(self.accept_states) + "\n"
        res += "sink states:\n"
        res += str(self.sink_name) + "\n"
        return res

    def runTimedWord(self, tws):
        """Execute the given timed words.
        
        tws : list(TimedWord)

        Returns whether the timed word is accepted (1), rejected (0), or goes
        to sink (-1).

        TODO: we currently only implement the deterministic case.

        """
        if tws in self.query:
            return self.query[tws]
        cur_state, cur_time = self.init_state, 0
        for tw in tws:
            moved = False
            for tran in self.trans:
                if tran.is_pass(cur_state, tw.action, cur_time + tw.time):
                    cur_state = tran.target
                    if tran.reset:
                        cur_time = 0
                    else:
                        cur_time += tw.time
                    moved = True
                    break
            if not moved:
                self.query[tws] = -1
                return -1  # assume to go to sink

        if self.sink_name is not None and cur_state == self.sink_name:            
            result = -1
        elif cur_state in self.accept_states:
            result = 1
        else:
            result = 0

        self.query[tws] = result
        return result


def OTAToJSON(ota, file_name):
    """Convert an OTA to a json file."""
    index_trans = {}
    if file_name is None:
        file_name = ota.name
    i = 0
    for tr in ota.trans:
        reset = "r" if tr.reset else "n"
        index_trans[str(i)] = [
            str(tr.source), str(tr.action), str(tr.constraint), str(reset), str(tr.target)
        ]
        i += 1

    ota_json = {
        "name": file_name,
        "sigma": [str(i) for i in ota.sigma],
        "accept": [str(i) for i in ota.accept_states],
        "init": str(ota.init_state),
        "l": [str(i.name) for i in ota.locations],
        "tran": index_trans
    }

    with open('./compare/%s.json' % file_name, 'w', encoding="utf-8") as f:
        json.dump(ota_json, f, indent=4)
        
def OTAToDOT(ota, file_name, keep_sink_location=False):
    """Convert an OTA to a dot file which can be used to draw by grahviz."""
    dot = Digraph()
    for location in ota.locations:
        if location.sink == True and keep_sink_location == False:
            continue
        if location.accept == True:
            dot.node(name=location.name, label=location.name, shape='doublecircle')
        else:
            dot.node(name=location.name, label=location.name)
    for tran in ota.trans:
        is_tran_contain_sink = False
        if tran.source == ota.sink_name or tran.target == ota.sink_name:
            is_tran_contain_sink = True
        if is_tran_contain_sink == True and keep_sink_location == False:
            continue
        tranLabel = " " + tran.action + " " + str(tran.constraint) + " " + str(tran.reset)
        dot.edge(tran.source, tran.target, tranLabel)
    # add a arrow to initial location
    dot.node(name="start", label="", shape='none')
    dot.edge("start", ota.init_state, "")
    # with open('./dot/%s.dot' % file_name, 'w', encoding="utf-8") as f:
    #     f.write(dot.source)
    dot.render('./dot/%s.dot' % file_name, format="png", view=True)

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

    assist_ota = OTA(assist_name, ota.sigma, assist_locations, assist_trans, assist_init, assist_accepts,
                     sink_name=sink.name)
    return assist_ota
