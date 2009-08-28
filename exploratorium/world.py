
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
    def __init__(self, terrainModel):
        self.terrainModel = terrainModel

    
