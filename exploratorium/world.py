
from pandac.PandaModules import OdeWorld, OdeQuadTreeSpace, OdeJointGroup

class World(object):

    def __init__(self, app):
        self.app = app
        self.physWorld = OdeWorld()
        self.physSpace = OdeQuadTreeSpace()
        self.physContactGroup = OdeJointGroup()
        
        self.physSpace.setAutoCollideWorld(self.odeWorld)
        self.physSpace.setAutoCollideJointGroup(self.physContactGroup)

class Cell(object):
    def __init__(self, cell, name, model, kind=None, collisionModel=None, physGeom=None):
        CollidableEntity.__init__(self, cell, name, model, kind, collisionModel, physGeom)
        self.terrainModel = model
        self.neighbours = { }
    def set_neighbour(self, key, obj):
        self.neighbours[key] = obj
    
