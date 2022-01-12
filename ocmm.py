# Mealy machine with one clock

import json
from interval import Interval, complement_intervals
from ota import Location

class IOTimedWord:
    """Timed word over input and output actions"""

    def __init__(self, input, output, time):
        """The initial data include:

        input : str, name of the input action.
        output: str, name of the output action.
        time : Decimal, logical clock value.

        """
        self.input = input
        self.output = output
        self.time = time

    def __eq__(self, other):
        return self.input == other.input and self.output == other.output and self.time == other.time

    def __le__(self, other):
        return (self.input, self.time, self.output) <= (other.input, other.time, other.output)

    def __lt__(self, other):
        return (self.input, self.time, self.output) < (other.input, other.time, other.output)

    def __hash__(self):
        return hash(('IOTIMEDWORD', self.input, self.output, self.time))

    def __str__(self):
        return '(%s,%s,%s)' % (self.input, self.output, str(self.time))

    def __repr__(self):
        return str(self)

class OCMMTran:
    """Represnt a transition in a Mealy machine with one clock"""

    def __init__(self, source, input, output, constraint, reset, target):
        """The initial data include:

        source : str, name of the source location.
        input : str, name of the input action.
        output : str, name of the output action.
        constraint : Interval, constraint of the transition.
        reset : bool, whether the transition resets the clock.
        target : str, name of the target location.

        """
        self.source = source
        self.input = input
        self.output = output
        self.constraint = constraint
        self.reset = reset
        self.target = target

    def __str__(self):
        return '%s %s %s %s %s %s' % (self.source, self.input, self.output, self.target, self.constraint, self.reset)

    def __repr__(self):
        return str(self)

    def is_pass(self, source, input, output, time):
        """Whether the given input/output actions and time is allowed by the transition.

        source : str, source of the input action.
        input : str, name of the input action.
        output : str, name of the output action.
        time : Decimal, time at which the input/output action should occur.

        """
        return source == self.source and input == self.input and output == self.output and\
            self.constraint.contains_point(time)
    
    def pass_input(self, source, input, time):
        """Whether the given input action and time is allowed by the transition.
        If allowed, return the output transition. Otherwise, return 'None'.
        """
        if source == self.source and input == self.input and self.constraint.contains_point(time):
            return self.output
        else:
            return None

class OCMM:
    """ Represent a Mealy machine with one clock"""

    def __init__(self, name, inputs, outputs, locations, trans, init_state, sink_name=None):
        """The initial data are:

        name : str, name of the automata.
        input : list(str), list of input actions.
        output: list(str), list of ooutput actions.
        locations : list(Location), list of locations.
        trans : list(OTATran), list of transitions.
        init_state : str, name of the initial locattion.
        sink_name ： str, name of the sink location.

        """
        self.name = name
        self.inputs = inputs
        self.outputs = outputs
        self.locations = locations
        self.trans = trans
        self.init_state = init_state
        self.sink_name = sink_name

        # store the runIOTimedWord result
        self.query = dict()
    
    def __str__(self):
        res = ""
        
        res += "OCMM name: \n"
        res += self.name + "\n"
        res += "Input actions and length of input actions: " + "\n"
        res += str(self.inputs) + " " + str(len(self.inputs)) + "\n"
        res += "Output actions and length of output actions: " + "\n"
        res += str(self.outputs) + " " + str(len(self.outputs)) + "\n"
        res += "Location (name, init, accept, sink) :\n"
        for l in self.locations:
            res += str(l) + "\n"
        res += "transitions (id, source_state, input, output, target_state, constraints, reset):\n"
        for t in self.trans:
            # if t.target != self.sink_name:
            res += "%s %s %s %s %s %s\n" % (t.source, t.input, t.output, t.target, t.constraint, t.reset)
        res += "init state:\n"
        res += str(self.init_state) + "\n"
        # res += "accept states:\n"
        # res += str(self.accept_states) + "\n"
        res += "sink states:\n"
        res += str(self.sink_name) + "\n"
        return res

    def runInputTimedWord(self, itws):
        """Execute the given timed word over inputs.
        itws : list of TimedWord over inputs.
        Return the output sequence. (Currently only implement the deterministic case.)
        """
        outputs = []
        cur_state, cur_time = self.init_state, 0
        for itw in itws:
            moved = False
            for tran in self.trans:
                output = tran.pass_input(cur_state, itw.action, cur_time + itw.time)
                if output != None:
                    outputs.append(output)
                    cur_state = tran.target
                    if tran.reset:
                        cur_time = 0
                    else:
                        cur_time += itw.time
                    moved = True
                    break
            if moved == False: # all transition go to sink location return the output 'void' for any inputs
                outputs.append('void')
        return outputs 

    # def runIOTimedWord(self, iotws):
    #     """Execute the given IO timed words.
        
    #     iotws : list(IOTimedWord)

    #     Returns whether the IO timed word is accepted (1), rejected (0), or goes
    #     to sink (-1).

    #     TODO: we currently only implement the deterministic case.

    #     """
    #     # if iotws in self.query:
    #     #     return self.query[iotws]
    #     cur_state, cur_time = self.init_state, 0
    #     for iotw in iotws:
    #         moved = False
    #         for tran in self.trans:
    #             if tran.is_pass(cur_state, iotw.input, iotw.output, cur_time + iotw.time):
    #                 cur_state = tran.target
    #                 if tran.reset:
    #                     cur_time = 0
    #                 else:
    #                     cur_time += iotw.time
    #                 moved = True
    #                 break
    #         if not moved:
    #             # self.query[iotws] = -1
    #             return -1  # assume to go to sink

    #     if self.sink_name is not None and cur_state == self.sink_name:            
    #         result = -1
    #     elif cur_state in self.accept_states:
    #         result = 1
    #     else:
    #         result = 0

    #     # self.query[iotws] = result
    #     return result

def buildOCMM(jsonfile):
    """Build the teacher OTA from a json file."""
    with open(jsonfile, 'r') as f:
        data = json.load(f)
        name = data["name"]
        locations_list = [l for l in data["l"]]
        inputs = [s for s in data["inputs"]]
        outputs = [s for s in data["outputs"]]
        trans_set = data["tran"]
        init_state = data["init"]
        # accept_list = [l for l in data["accept"]]
        L = [Location(location, False, False) for location in locations_list]
        for l in L:
            if l.name == init_state:
                l.init = True
            # if l.name in accept_list:
            #     l.accept = True
        trans = []
        for tran in trans_set:
            source = trans_set[tran][0]
            input = trans_set[tran][1]
            output = trans_set[tran][2]
            constraint = Interval(trans_set[tran][3])
            reset = (trans_set[tran][4] == 'r')
            target = trans_set[tran][5]
            ocmm_tran = OCMMTran(source, input, output, constraint, reset, target)
            trans.append(ocmm_tran)
        return OCMM(name, inputs, outputs, L, trans, init_state)

def buildAssistantOCMM(ocmm):
    """Add the sink location to an OCMM, return the completed OCMM.
    """
    location_number = len(ocmm.locations)
    tran_number = len(ocmm.trans)
    sink = Location(str(location_number+1), False, False, True)

    new_trans = []
    for l in ocmm.locations:
        # Mapping from inputs to list of transitions from l with the input.
        l_dict = {}
        for key in ocmm.inputs:
            l_dict[key] = []

        for tran in ocmm.trans:
            if tran.source == l.name:
                l_dict[tran.input].append(tran.constraint)

        for key in l_dict:
            cuintervals = []
            if len(l_dict[key]) > 0:
                cuintervals = complement_intervals(l_dict[key])
            else:
                cuintervals = [Interval("[0,+)")]
            if len(cuintervals) > 0:
                for c in cuintervals:
                    new_trans.append(OCMMTran(l.name, key, 'void', c, True, sink.name))

    assist_name = "Assist_" + ocmm.name
    assist_locations = [location for location in ocmm.locations]
    assist_trans = [tran for tran in ocmm.trans]
    assist_init = ocmm.init_state
    assist_outputs = [o for o in ocmm.outputs]
    # assist_accepts = [sn for sn in ota.accept_states]
    if len(new_trans) > 0:
        # Add sink location
        assist_locations.append(sink)

        # Add empty action 'void' to ocmm.outputs
        if 'void' not in ocmm.outputs:
            assist_outputs.append('void')

        # Add transitions from normal locations to sink
        assist_trans.extend(new_trans)

        # Add loops from sink to sink
        for label in ocmm.inputs:
            assist_trans.append(OCMMTran(sink.name, label, 'void', Interval("[0,+)"), True, sink.name))

    assist_ocmm = OCMM(assist_name, ocmm.inputs, assist_outputs, assist_locations, assist_trans, assist_init, sink_name=sink.name)
    return assist_ocmm
