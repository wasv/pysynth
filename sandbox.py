import sys
import math
import struct

import operator as Op
import itertools as I
import functools as F

from tempfile import TemporaryFile

class BaseNode:
    framerate = 192000

    def __call__(self, signal=None, **kwargs):
        if signal:
            if not callable(signal):
                try:
                    iter(signal)
                except TypeError:
                    raise TypeError("{} is not a signal type.".format(type(signal)))
            self.sink(signal, **kwargs)
        return self.source()

    def sink(self, signal):
        raise Exception("{} has no sink.".format(type(self)))

    def source(self):
        return None

class ConstantNode(BaseNode):
    def __init__(self, value=1):
        self.value = value

    def source(self):
        while True:
            yield self.value

class SineNode(BaseNode):
    def __init__(self, freq=440):
        self.freq = freq

    def source(self):
        for i in I.count(1):
            yield math.sin((i/self.framerate)*math.tau*self.freq)

class ModNode(BaseNode):
    def __init__(self, freq=60):
        self.freq = freq
        self._sink = None

    def sink(self, signal):
        self._sink = signal

    def source(self):
        lpf = 0.1
        fdeviation = 0.0
        dc_comp = 0.0
        for i in I.count(1):
            ampl = next(self._sink)
            dc_comp = (1.0-lpf) * dc_comp + lpf * ampl - (dc_comp/i)
            fdeviation += ampl - dc_comp
            yield math.cos(math.tau*(i/self.framerate)*self.freq + fdeviation)

class MixNode(BaseNode):

    def __init__(self):
        self._sinks = []
        self._weights = []

    def sink(self, signal, weight=1):
        self._sinks.append(signal)
        self._weights.append(weight)

    def source(self):
        mag = sum(self._weights)
        if mag > 1.0:
            weights = [ n/mag for n in self._weights ]
        else:
            weights = self._weights

        while True:
            yield sum(map(Op.mul,map(next,self._sinks),weights))

class DumpNode(BaseNode):
    def __init__(self):
        self._sink = None

    def sink(self, signal):
        self._sink = signal

    def dump(self, output, duration=1):
        numsamples = int(duration * self.framerate)

        for sample in I.islice(self._sink, numsamples):
            if sample > 1: sample = 1.0
            if sample < -1: sample = -1.0
            frame = struct.pack('f', sample)
            output.write(frame)

def harmony(f0=440,nharmonics=3):
    mixer = MixNode()

    for h in range(1,nharmonics+1):
        tone = SineNode(f0*h)
        mixer(tone())

    return mixer


def _main(outfile):
    osc0 = ConstantNode(1)
    osc1 = harmony(360,2)
    osc2 = harmony(640,2)
    osc = SineNode(440)
    mod = ModNode(4)

    mixer = MixNode()

    out = DumpNode()

    mixer(osc2())
    mixer(osc0())

    out(mod(mixer()))

    out.dump(outfile,10)


if __name__ == "__main__":
    from sys import argv
    if len(argv) == 2:
        outfile = open(argv[1], 'wb')
    else:
        outfile = TemporaryFile()
    _main(outfile)
    outfile.close()
