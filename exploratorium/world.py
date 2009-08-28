
from pandac.PandaModules import OdeWorld, OdeSpace, OdeJointGroup

class World(object):

    def __init__(self, app):
        self.app = app
        self.physWorld = OdeWorld()
        self.physSpace = OdeSimpleSpace()


class Cell(object):
    def __init__(self, terrainModel):
        
