
from pandac.PandaModules import OdeWorld, OdeQuadTreeSpace, OdeJointGroup

class World(object):

    def __init__(self, app):
        self.app = app
        self.physWorld = OdeWorld()
        self.physSpace = OdeQuadTreeSpace()
        self.physContactGroup = OdeJointGroup()
        
        self.physSpace.setAutoCollideWorld(self.odeWorld)
        self.physSpace.setAutoCollideJointGroup(self.physContactGroup)
        
        self.cellList = { }
        self.addCell('root',Cell(self, "root", 0))
    
    def addCell(self,name,obj):
        self.cellList[name] = obj
    
    def addCellNeighbour(self,name,key,neighbour):
        self.cellList[name].setNeighbour(key,neighbour)
    
    def addCellNeighbour(self,name,neighbours):
        self.cellList[name].setNeighbour(neighbours)
    
    def getCell(self,name):
        return self.cellList[name]
    
    def getCellNeighbours(self,name):
        return self.cellList[name].getNeighbours()
    
    def getRoot(self):
        return self.cellList['root']
        
    

class Cell(object):
    def __init__(self, world, name, model, kind=None, collisionModel=None, physGeom=None):
        self._world = world
        CollidableEntity.__init__(self, cell, name, model, kind, collisionModel, physGeom)  
        self.neighbours = { }
        
    def setNeighbour(self, key, obj):
        self.neighbours[key] = obj
        
    def setNeighbour(self, objs):
        self.neighbours = objs
    
    def getNeighbours(self):
        return self.neighbours
    
