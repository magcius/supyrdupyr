
from supyrdupyr.world import World as sdWorld
from exploratorium.levels.devterrain import DevTerrain

class World(sdWorld):

    def setupWorld(self):
        self.terrain = DevTerrain(self)
