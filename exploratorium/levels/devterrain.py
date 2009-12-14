
from supyrdupyr.entities import StaticEntity, PhysicsEntity

class DevTerrain(StaticEntity):
    def __init__(self, world):
        super(DevTerrain, self).__init__(world, "DevTerrain", (0, 0, 0), "devcell.mesh", "terrain dev", mass=5)
        print self.sceneNode.showBoundingBox(True)
