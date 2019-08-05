import sys
import math
import struct

import operator as Op
import itertools as I
import functools as F

from tempfile import TemporaryFile

class BaseNode:
    framerate = 44100
    sampwidth = 2
    
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
        for i in I.count(0):
            yield math.sin((i/self.framerate)*math.tau*self.freq)

class MixNode(BaseNode):
    _sinks = []
    _weights = []

    def sink(self, signal, weight=1):
        self._sinks.append(signal)
        self._weights.append(weight)
    
    def source(self):
        mag = sum(self._weights)
        if mag > 1:
            weights = [ n/mag for n in self._weights]
            
        while True:
            yield sum(map(Op.mul,map(next,self._sinks),self._weights))

class DumpNode(BaseNode):
    _sink = None
    
    def sink(self, signal):
        self._sink = signal

    def dump(self, output, duration=1):
        max_amplitude = float(int((2 ** (self.sampwidth * 8)) / 2) - 1)
        numsamples = int(duration * self.framerate)

        for sample in I.islice(self._sink, numsamples):
            if sample > 1: sample = 1
            if sample < -1: sample = -1
            frame = struct.pack('h', int(max_amplitude * sample))
            output.write(frame)


def _main(outfile):
    null = ConstantNode(0)
    osc = SineNode(4410)
    mixer = MixNode()
    out = DumpNode()

    mixer(osc())

    out(mixer())

    out.dump(outfile)
    

if __name__ == "__main__":
    from sys import argv
    if len(argv) == 2:
        outfile = open(argv[1], 'wb')
    else:
        outfile = TemporaryFile()
    _main(outfile)
    outfile.close()
