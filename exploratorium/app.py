
import os
import os.path
import sys

if __name__ == "__main__":
    sys.path.append("..")

from supyrdupyr.baseapp import BaseApplication
from exploratorium.world import World
from exploratorium.hero import Hero

class Exploratorium(BaseApplication):

    debugLogging = True
    
    def createWorld(self):
        self.camera.setNearClipDistance(0.1)
        self.world = World(self)
        self.hero = Hero(self.world)

if __name__ in ("__supyrdupyr__", "__main__"):
    app = Exploratorium()
    app.go()
