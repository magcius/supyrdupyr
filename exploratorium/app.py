
import os
import os.path
import sys

if __name__ == "__main__":
    sys.path.append("..")

from supyrdupyr.baseapp import BaseApplication
from exploratorium.world import World
from exploratorium.hero import ExplrHero

class Exploratorium(BaseApplication):

    debugLogging = True
    
    def createScene(self):
        BaseApplication.createScene(self)
        self.world = World(self)
        self.hero = ExplrHero()

if __name__ in ("__supyrdupyr__", "__main__"):
    app = Exploratorium()
    app.go()
