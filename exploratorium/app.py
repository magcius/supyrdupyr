

import direct.directstart.directstart
from direct.task import task
from exploratorium import states

STATE_MAP = {
    "splash": states.SplashState,
    "menu"  : states.MenuState,
    "game"  : states.GameState
}

class Application(object):
    
    def __init__(self):
        self.change_state("game")

    def change_state(self, state):
        if self.state.name != state:
            self.state.cleanup()
            self.state = STATE_MAP[state](app=self)

    def run(self):
        run()
