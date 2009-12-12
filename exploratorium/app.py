
import os.path

from supyrdupyr.baseapp import BaseApplication
from exploratorium.world import World
from exploratorium.entities import hero

class Exploratorium(BaseApplication):
    def createScene(self):
        BaseApplication.createScene(self)
        self.world = World(self)

    def createMessengerListeners(self):
        pass
    

if __name__ == "__supyrdupyr__":
    app = Exploratorium()
    app.go()
