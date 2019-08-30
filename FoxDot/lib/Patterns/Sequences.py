"""
Sequences.py
------------
All patterns inherit from Base.Pattern. There are two types of pattern:

1. Container types
    * Similar to lists but with different mathematical operators
2. Generator types
    * Similar to generators but can be indexed (returns values based on functions)
"""

from __future__ import absolute_import, division, print_function

import random
import math

from .Main import *
from .PGroups import *
from .Operations import *
from .Generators import PRand

MAX_SIZE = 2048

#==============================#
#         1. P[] & P()         #
#==============================#

class __pattern__(object):
    ''' Used to define lists as patterns:

        `P[1,2,3]` is equivalent to `Pattern([1,2,3])` and
        `P(1,2,3)` is equivalent to `Pattern((1,2,3))` and
        `P+(1,2,3)` is equivalient to `Pattern((1,2,3))`.

        Ranges can be created using slicing, e.g. `P[1:6:2]` will generate the range
        1 to 6 in steps of 2, thus creating the Pattern `[1, 3, 5]`. Slices can be
        combined with other values in a Pattern such that `P[0,2,1:10]` will return
        the Pattern `P[0, 2, 1, 2, 3, 4, 5, 6, 7, 8, 9]`
    '''
    def __getitem__(self, args):
        if isinstance(args, Pattern):
            return args
        elif isinstance(args, (Pattern.TimeVar, Pattern.PlayerKey)):
            data = [args]
        elif hasattr(args, '__iter__') and not isinstance(args, (str, bytes, GeneratorPattern, PGroup)):
            data = []
            for item in args:
                if type(item) is slice:
                    data.extend(sliceToRange(item))
                else:
                    data.append(item)
        elif type(args) is slice:
            data = sliceToRange(args)
        else:
            data = args
        return Pattern(data)

    def __call__(self, *args):
        return PGroup(args if len(args) > 1 else args[0])

    def __mul__(self, other):
        """ P*[0,1,2] returns PRand([0,1,2])
            P*(0,1,2) returns PGroupStar(0,1,2)
        """
        if isinstance(other, (list, Pattern)):
            return PRand(list(other))
        else:
            return PGroupStar(other)

    def __pow__(self, other):
        """ P**(x1, x2,...,xn) - Returns scrambled version """
        return PGroupPow(other)

    def __xor__(self, other):
        """ P^(x1, x2,..., dur) -  Returns a PGroup that delays each value by dur * n """
        return PGroupXor(other)

    def __or__(self, other):
        """ P|("x", 2) """
        return PGroupOr(other)

    def __add__(self, other):
        return PGroupPlus(other)

    def __radd__(self, other):
        return self + other

    def __truediv__(self, other):
        return PGroupDiv(other)

    def __mod__(self, other):
        if isinstance(other, list):
            return Pattern().fromString(other[0], flat=True)
        return PGroupMod(other)

    def __and__(self, other):
        return PGroupAnd(other)

    def __invert__(self):
        return __reverse_pattern__()

class __reverse_pattern__(__pattern__):
    def __getattr__(self, name):
        return ~object.__getattr__(self, name)


# This is a pattern creator
P = __pattern__()

#================================#
#      2. Pattern Functions      #
#================================#

#: Pattern functions that take patterns as arguments

def PShuf(seq):
    ''' PShuf(seq) -> Returns a shuffled version of seq'''
    return Pattern(seq).shuffle()

def PAlt(pat1, pat2, *patN):
    ''' Returns a Pattern generated by alternating the values in the given sequences '''
    data = []
    item = [asStream(p) for p in [pat1, pat2] + list(patN)]
    size = LCM(*[len(i) for i in item])
    for n in range(size):
        for i in item:
            data.append(modi(i,n))
    return Pattern(data)

def PStretch(seq, size):
    ''' Returns 'seq' as a Pattern and looped until its length is 'size'
        e.g. `PStretch([0,1,2], 5)` returns `P[0, 1, 2, 0, 1]` '''
    return Pattern(seq).stretch(size)

def PPairs(seq, func=lambda n: 8-n):
    """ Laces a sequence with a second sequence obtained
        by performing a function on the original. By default this is
        `lambda n: 8 - n`. """
    i = 0
    data = []
    for item in seq:
        data.append(item)
        data.append(func(item))
        i += 1
        if i >= MAX_SIZE:
            break
    return Pattern(data)

def PZip(pat1, pat2, *patN):
    ''' Creates a Pattern that 'zips' together multiple patterns. `PZip([0,1,2], [3,4])`
        will create the Pattern `P[(0, 3), (1, 4), (2, 3), (0, 4), (1, 3), (2, 4)]` '''
    l, p = [], []
    for pat in [pat1, pat2] + list(patN):
        p.append(P[pat])
        l.append(len(p[-1]))
    length = LCM(*l)
    return Pattern([tuple(pat[i] for pat in p) for i in range(length)])


def PZip2(pat1, pat2, rule=lambda a, b: True):
    ''' Like `PZip` but only uses two Patterns. Zips together values if they satisfy the rule. '''
    length = LCM(len(pat1), len(pat2))
    data = []
    i = 0
    while i < length:
        a, b = modi(pat1,i), modi(pat2,i)
        if rule(a, b):
            data.append((a,b))
        i += 1
    return Pattern(data)

@loop_pattern_func
def PStutter(x, n=2):
    """ PStutter(seq, n) -> Creates a pattern such that each item in the array is repeated n times (n can be a pattern) """
    return Pattern([x for i in range(n)])

@loop_pattern_func
def PSq(a=1, b=2, c=3):
    ''' Returns a Pattern of square numbers in the range a to a+c '''
    return Pattern([x**b for x in range(a,a+c)])

@loop_pattern_func
def P10(n):
    ''' Returns an n-length Pattern of a randomly generated series of 1's and 0's '''
    return Pattern([random.choice((0,1)) for i in range(int(n))])

@loop_pattern_func
def PStep(n, value, default=0):
    ''' Returns a Pattern that every n-term is 'value' otherwise 'default' '''
    return Pattern([default] * (n-1) + [value])

@loop_pattern_func
def PSum(n, total, **kwargs):
    """
    Returns a Pattern of length 'n' that sums to equal 'total'

    e.g. PSum(3,8) -> P[3, 3, 2]
         PSum(5,4) -> P[1, 0.75, 0.75, 0.75, 0.75]
    """
    lim = kwargs.get("lim", 0.125)

    data = [total + 1]

    step = 1
    while sum(data) > total:
        data = [step for x in range(n)]
        step *= 0.5

    i = 0
    while sum(data) < total and step >= lim:
        if sum(data) + step > total:
            step *= 0.5
        else:
            data[i % n] += step
            i += 1

    return Pattern(data)

@loop_pattern_func
def PRange(start, stop=None, step=None):
    """ Returns a Pattern equivalent to ``Pattern(range(start, stop, step))`` """
    return Pattern(list(range(*[val for val in (start, stop, step) if val is not None])))

@loop_pattern_func
def PTri(start, stop=None, step=None):
    """ Returns a Pattern equivalent to ``Pattern(range(start, stop, step))`` with its reversed form
    appended."""
    pat = PRange(start, stop, step)
    return pat | pat.reverse()[1:-1]

@loop_pattern_func
def PSine(n=16):
    """ Returns values of one cycle of sine wave split into 'n' parts """
    i = (2 * math.pi) / n
    return Pattern([math.sin(i * j) for j in range(int(n))])

@loop_pattern_func
def PEuclid(n, k):
    ''' Returns the Euclidean rhythm which spreads 'n' pulses over 'k' steps as evenly as possible.
        e.g. `PEuclid(3, 8)` will return `P[1, 0, 0, 1, 0, 0, 1, 0]` '''
    return Pattern( EuclidsAlgorithm(n, k) )

@loop_pattern_func
def PEuclid2(n, k, lo, hi):
    ''' Same as PEuclid except it returns an array filled with 'lo' value instead of 0
        and 'hi' value instead of 1. Can be used to generate characters patterns used to
        play sample like play(PEuclid2(3,8,'-','X')) will be equivalent to
        play(P['X', '-', '-', 'X', '-', '-', 'X', '-'])
        that's like saying play("X--X--X-")
        '''
    return Pattern( EuclidsAlgorithm(n, k, lo, hi) )

@loop_pattern_func
def PBern(size=16, ratio=0.5):
    """ Returns a pattern of 1s and 0s based on the ratio value (between 0 and 1).
        This is called a Bernoulli sequence. """
    return Pattern([int(random.random() < ratio) for n in range(size)])


def PBeat(string, start=0, dur=0.5):
    """ Returns a Pattern of durations based on an input string where
        non-whitespace denote a pulse e.g.
        ::

            >>> PBeat("x xxx x")
            P[1, 0.5, 0.5, 1, 0.5]
    """
    data = [int(char != " ") for char in list(string)]
    pattern = Pattern(PulsesToDurations( data ))
    if start != 0:
        pattern = pattern.rotate(int(start))
    return pattern * dur

@loop_pattern_func
def PDur(n, k, start=0, dur=0.25):
    """ Returns the *actual* durations based on Euclidean rhythms (see PEuclid) where dur
        is the length of each step.
        ::
            >>> PDur(3, 8)
            P[0.75, 0.75, 0.5]
            >>> PDur(5, 16)
            P[0.75, 0.75, 0.75, 0.75, 1]
    """
    # If we have more pulses then steps, double the steps and decrease the duration

    while n > k:
        k   = k * 2
        dur = dur / 2

    pattern = Pattern(PulsesToDurations( EuclidsAlgorithm(n, k) ))
    if start != 0:
        pattern = pattern.rotate(int(start))
    return pattern * dur

@loop_pattern_func # forces it into a stream instead of Group
def PDelay(*args):
    return PDur(*args).accum().group()

@loop_pattern_func
def PStrum(n=4):
    """ Returns a pattern of durations similar to how you might strum a guitar """
    return (Pattern([1,1/2]).stutter([1,n + 1])|Pattern([1.5,1/2]).stutter([1,n])|1)

def PQuicken(dur=1/2, stepsize=3, steps=6):
    """ Returns a PGroup of delay amounts that gradually decrease """
    delay = []
    count = 0
    for i in range(steps):
        for j in range(stepsize-1):
            delay.append( count )
            count += dur / stepsize
        dur /= stepsize
    return PGroup(delay)


def PRhythm(durations):
    """ Converts all tuples/PGroups into delays calculated using the PDur algorithm.
    e.g.
        PRhythm([1,(3,8)]) -> P[1,(2,0.75,1.5)]
    *work in progress*
    """
    if len(durations) == 1:
        item = durations[0]
        if isinstance(item, (tuple, PGroup)):
            return PDur(*item)
        else:
            return durations
    else:
        durations = asStream(durations).data
        output = Pattern()
        for i in range(len( asStream(durations).data ) ):
            item = durations[i]
            if isinstance(item, (list, Pattern)):
                value = PRhythm(item)
            elif isinstance(item, (tuple, PGroup)):
                dur   = PDur(*item)
                value = PGroup(sum(dur)|dur.accum()[1:])
            else:
                value = item
            output.append(value)
        return output


def PJoin(patterns):
    """ Joins a list of patterns together """
    data = []
    for pattern in patterns:
        data.extend(pattern)
    return Pattern(data)
