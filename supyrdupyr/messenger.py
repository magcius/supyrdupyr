
from supyrdupyr.util import methodSignature

class Messenger(object):

    def __init__(self, app):
        self.app = app
        self.registry = dict()

    def accept(self, eventName, function, extraArgs=[], extraKwargs={}, priority=10):
        if self.app.debugLogging:
            print "Accepting %s for event '%s'" % (methodSignature(function, extraArgs, extraKwargs), eventName)
        self.registry.setdefault(eventName, [])
        # Sort by priority, then order of addition.
        self.registry[eventName].append((priority, len(self.registry[eventName]), function, extraArgs, extraKwargs))
        self.registry[eventName].sort()

    def send(self, eventName, args=[], kwargs={}):
        functions = self.registry.get(eventName, [])
        for _, __, function, args_, kwargs_ in functions:
            args_ += args
            kwargs_.update(kwargs)
            if self.app.debugLogging:
                print "Calling %s for event '%s'" % (methodSignature(function, args_, kwargs_), eventName)
            function(*args, **kwargs)
