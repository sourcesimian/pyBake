import inspect

class Foo(object):
    m = None

    def __init__(self):
        self.m = 'init'

    def file(self):
        return __file__

    def src(self):
        return inspect.getsourcefile(self.__class__)

    def bang(self):
        self._bang()

    def _bang(self):
        raise ValueError('from Foo')
