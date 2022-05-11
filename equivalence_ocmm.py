"""Simple version of equivalence test, for deterministic one-clock
timed automata.

"""

import queue
from decimal import Decimal

import ota
import interval
from equivalence_simple import round_div_2, dec_zero, \
    dec_half, dec_one, EQ, LESS, GREATER

class Configuration:
    """A configuration consists of states for the left and right timed
    automata. Each state consists of location and region. If both sides
    are in fraction regions, then an additional boolean variable indicates
    whether the left automata has smaller fraction value.
    
    Region is indicated by a single integer. The value 2 * n indicates
    the point region [n, n]. The value 2 * n + 1 indicates the region
    (n, n+1). The last region is 2 * max_value + 1, indicating the region
    (max_value, oo).

    pre - previous configuration.
    action - decimal number for delay, or string for name of an action.

    """
    def __init__(self, loc_A, region_A, output_A, loc_B, region_B, output_B, frac_A, frac_B, *, pre=None, action=None):
        self.loc_A = loc_A
        self.region_A = region_A
        self.output_A = output_A
        self.loc_B = loc_B
        self.region_B = region_B
        self.output_B = output_B
        self.frac_A = frac_A
        self.frac_B = frac_B
        
        # For reconstructing the path
        self.pre = pre
        self.action = action

    def __eq__(self, other):
        return self.loc_A == other.loc_A and self.region_A == other.region_A and \
               self.loc_B == other.loc_B and self.region_B == other.region_B and \
               self.output_A == other.output_A and self.output_B == other.output_B and \
               (self.frac_A == other.frac_A and self.frac_B == other.frac_B or \
                self.frac_A < self.frac_B and other.frac_A < other.frac_B or \
                self.frac_A > self.frac_B and other.frac_A > other.frac_B)

    def __str__(self):
        return "loc_A: %s region_A: %s output_A: %s loc_B: %s region_B: %s output_B: %s frac_A: %s frac_B: %s \n(pre: %s action: %s)" % (
            self.loc_A, self.region_A, self.output_A, self.loc_B,
             self.region_B, self.output_B, self.frac_A, self.frac_B, self.pre, self.action)

    def __hash__(self):
        if self.frac_A < self.frac_B:
            return hash(("CONFIG", self.loc_A, self.region_A, self.output_A, 
                self.loc_B, self.region_B, self.output_B, LESS))
        elif self.frac_A == self.frac_B:
            return hash(("CONFIG", self.loc_A, self.region_A, self.output_A, 
                self.loc_B, self.region_B, self.output_B, EQ))
        elif self.frac_A > self.frac_B:
            return hash(("CONFIG", self.loc_A, self.region_A, self.output_A, 
                self.loc_B, self.region_B, self.output_B, GREATER))
        else:
            raise ValueError

class OCMMEquivalence:
    def __init__(self, max_value, ocmm_A, ocmm_B):
        self.max_value = max_value
        self.ocmm_A = ocmm_A
        self.ocmm_B = ocmm_B
        assert ocmm_A.sigma == ocmm_B.sigma, "OCMMEquivalence: OTAs must have the same actions."
        assert ocmm_A.outputs == ocmm_B.outputs, "OCMMEquivalence: OCMMs must have the same outputs."

        self.init_config = Configuration(
            self.ocmm_A.init_state, 0, tuple(), self.ocmm_B.init_state, 0, tuple(), dec_zero, dec_zero)

        # Mapping from n to region
        self.region_dict = dict()

    def int_to_region(self, n):
        if n in self.region_dict:
            return self.region_dict[n]
        elif n % 2 == 0:
            self.region_dict[n] = interval.point_region(n // 2)
        elif n == 2 * self.max_value + 1:
            self.region_dict[n] = interval.inf_region(self.max_value)
        else:
            self.region_dict[n] = interval.frac_region(n // 2)

        return self.region_dict[n]

    def is_inf(self, n):
        return n == 2 * self.max_value + 1

    def is_point(self, n):
        return n % 2 == 0

    def is_frac(self, n):
        return n % 2 == 1

    def delay_one(self, c):
        """Delay the given configuration by the minimal time. Return the new
        configuration, as well as a time increment.
        
        """
        if self.is_inf(c.region_A):
            if self.is_point(c.region_B):
                return Configuration(c.loc_A, c.region_A, c.output_A, 
                        c.loc_B, c.region_B+1, c.output_B, dec_zero, dec_half), dec_half
            else:
                return Configuration(c.loc_A, c.region_A, c.output_A, 
                    c.loc_B, c.region_B+1, c.output_B, dec_zero, dec_zero), 1 - c.frac_B
        elif self.is_inf(c.region_B):
            if self.is_point(c.region_A):
                return Configuration(c.loc_A, c.region_A+1, c.output_A, 
                    c.loc_B, c.region_B, c.output_B, dec_half, dec_zero), dec_half
            else:
                return Configuration(c.loc_A, c.region_A+1, c.output_A, 
                    c.loc_B, c.region_B, c.output_B, dec_zero, dec_zero), 1 - c.frac_A
        elif self.is_point(c.region_A) and self.is_point(c.region_B):
            return Configuration(c.loc_A, c.region_A+1, c.output_A, 
                c.loc_B, c.region_B+1, c.output_B, dec_half, dec_half), dec_half
        elif self.is_point(c.region_A) and self.is_frac(c.region_B):
            inc = round_div_2(dec_one - c.frac_B)
            return Configuration(c.loc_A, c.region_A+1, c.output_A, 
                c.loc_B, c.region_B, c.output_B, inc, c.frac_B + inc), inc
        elif self.is_frac(c.region_A) and self.is_point(c.region_B):
            inc = round_div_2(dec_one - c.frac_A)
            return Configuration(c.loc_A, c.region_A, c.output_A, 
                c.loc_B, c.region_B+1, c.output_B, c.frac_A + inc, inc), inc
        elif self.is_frac(c.region_A) and self.is_frac(c.region_B):
            if c.frac_A == c.frac_B:
                return Configuration(c.loc_A, c.region_A+1, c.output_A, 
                    c.loc_B, c.region_B+1, c.output_B, dec_zero, dec_zero), 1 - c.frac_A
            elif c.frac_A < c.frac_B:
                inc = dec_one - c.frac_B
                return Configuration(c.loc_A, c.region_A, c.output_A, 
                    c.loc_B, c.region_B+1, c.output_B, c.frac_A + inc, dec_zero), inc
            else:  # c.frac_A > c.frac_B
                inc = dec_one - c.frac_A
                return Configuration(c.loc_A, c.region_A+1, c.output_A, 
                    c.loc_B, c.region_B, c.output_B, dec_zero, c.frac_B + inc), inc
        else:
            raise AssertionError

    def delay_seq(self, c):
        """Obtain the sequence of delays from given configuration."""
        results = [Configuration(c.loc_A, c.region_A, c.output_A, 
                    c.loc_B, c.region_B, c.output_B, c.frac_A, c.frac_B, pre=c, action=dec_zero)]
        inc_total = dec_zero
        cur_config = c
        while not (self.is_inf(cur_config.region_A) and self.is_inf(cur_config.region_B)):
            cur_config, inc = self.delay_one(cur_config)
            inc_total = inc_total + inc
            cur_config.pre = c
            cur_config.action = inc_total
            results.append(cur_config)
        return results

    def is_bad(self, c):
        """Determine whether c is a bad state. That is A side is accepting
        but B side is not accepting, or vice versa.
        
        """
        return c.output_A != c.output_B
    
    def immediate_asucc(self, c, action):
        """Perform an immediate action, without further time delays."""
        A_tran, B_tran = None, None
        A_reg = self.int_to_region(c.region_A)
        B_reg = self.int_to_region(c.region_B)

        for tran in self.ocmm_A.trans_dict[(action, c.loc_A)]:
            if tran.constraint.contains_interval(A_reg):
                A_tran = tran
                break
        for tran in self.ocmm_B.trans_dict[(action, c.loc_B)]:
            if tran.constraint.contains_interval(B_reg):
                B_tran = tran
                break
        assert A_tran is not None and B_tran is not None

        new_region_A = 0 if A_tran.reset else c.region_A
        new_frac_A = dec_zero if A_tran.reset else c.frac_A
        new_region_B = 0 if B_tran.reset else c.region_B
        new_frac_B = dec_zero if B_tran.reset else c.frac_B
        seq= self.find_path(c)
        return Configuration(A_tran.target, new_region_A, self.ocmm_A.runTimedWord, 
                B_tran.target, new_region_B, B_tran.output, 
                    new_frac_A, new_frac_B, pre=c, action=action)

    def compute_wsucc(self, c):
        """Compute the list of all successors of c."""
        delay_seq = self.delay_seq(c)
        results = []
        for delay in delay_seq:
            for action in self.ocmm_A.sigma:
                imm_asucc = self.immediate_asucc(delay, action)
                if imm_asucc not in results:
                    results.append(imm_asucc)
        return results

    def find_path(self, c):
        """Return the timed word reaching self."""

        tws = []
        while c != self.init_config:
            assert isinstance(c.action, str), 'find_path'
            action = c.action
            c = c.pre
            assert isinstance(c.action, Decimal), 'find_path'
            time = c.action
            c = c.pre
            tws.append(ota.TimedWord(action, time))
        return tuple(reversed(tws))

    def test_equivalent(self):
        to_explore = queue.Queue()
        explored = set()
        to_explore.put(self.init_config)

        while True:
            if to_explore.empty():
                return True, None

            c = to_explore.get()
            assert c.output_A == c.output_B
            if c in explored:
                continue
            explored.add(c)

            wsucc = self.compute_wsucc(c)
            for nw in wsucc:
                if self.is_bad(nw):
                    return False, self.find_path(nw)

                if nw not in explored:
                    to_explore.put(nw)
