
from supyrdupyr.entities.base import LogicEntity

class TimerEntity(LogicEntity):
    def __init__(self, world, name, interval, tags=""):
        super(TimerEntity, self).__init__(world, name, "logic timer " + tags)
        self.enabled = False
        self.interval = interval
        self.timeElapsed = 0
        self.lastTimeElapsed = 0
        self.highLow = "High"

    def simulate(self, dt):
        if self.enabled:
            self.timeElapsed += dt
            if (self.timeElapsed - self.lastTimeElapsed) % self.interval > 0:
                self.lastTimeElapsed = self.timeElapsed
                self.fireTimer()

    def reset(self, value):
        self.timeElapsed = 0
        self.lastTimeElapsed = 0

    def setInterval(self, value):
        self.reset()
        self.interval = value[0]

    def toggle(self, value):
        self.reset()
        super(TimerEntity, self).toggle()

    def setHigh(self, value):
        self.highLow = "High"

    def setLow(self, value):
        self.highLow = "Low"

    def fireTimer(self):
        args = [int(self.timeElapsed % self.interval), self.timeElapsed]
        self.fireOutput("OnTimer", args)
        self.fireOutput("OnTimer" + self.highLow, args)
        
    def setupIO(self):
        self.bindOutput("OnTimerHigh", self, "SetLow")
        self.bindOutput("OnTimerLow", self, "SetHigh")

    inputHandlers = {
        "Reset": reset,
        "FireTimer": fireTimer,
        "RefireTime": setInterval,
        "Toggle": toggle,
        "SetHigh": setHigh,
        "SetLow": setLow,
    }

    inputSpec = {
        "Reset": (None, "Start the timer back at 0."),
        "FireTimer": (None, "Force the timer to fire immediately"),
        "RefireTime": ([int], "Set the time in between timer ticks"),
        "Toggle": (None, "Turn the timer on and off, resetting it in the process"),
        "SetHigh": (None, "Set the timer's oscillator to \"High\""),
        "SetLow": (None, "Set the timer's oscillator to \"Low\""),
    }

    outputSpec = {
        "OnTimer": ([int, float], "Fired when the timer has elapsed. Arguments are [count, timeElapsed]."),
        "OnTimerHigh": ([int, float], "Fired when the timer has elapsed, alternating between High and Low, starting with High. Arguments are [count, timeElapsed]."),
        "OnTimerLow": ([int, float], "Fired when the timer has elapsed, alternating between High and Low, starting with High. Arguments are [count, timeElapsed]."),
    }
