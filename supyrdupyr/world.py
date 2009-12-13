
from supyrdupyr.entities import PhysicsEntity
from supyrdupyr.util import diagonal
from supyrdupyr import messenger, entities
from ogre.physics import bullet
from ogre.io import OIS
import ogre.renderer.OGRE as ogre

class WorldFrameListener(ogre.FrameListener):
    def __init__(self, world):
        self.world = world
        ogre.FrameListener.__init__(self)
    
    def frameStarted(self, evt):
        self.world.updateWorld(evt.timeSinceLastFrame)
        return True

class World(object):
    
    cellSize    = 512
    cellMap     = []
    
    def __init__(self, app):
        self.app = app
        
        app.world = self

        self.frameListener = WorldFrameListener(self)
        app.root.addFrameListener(self.frameListener)
        self.worldNode = app.sceneManager.getRootSceneNode().createChildSceneNode("World")
        
        self.physCollisionConfiguration = bullet.btDefaultCollisionConfiguration() 
        self.physDispatcher = bullet.btCollisionDispatcher (self.physCollisionConfiguration)
        
        self.physBroadphase = bullet.btDbvtBroadphase()
        self.physBroadphase.getOverlappingPairCache().setInternalGhostPairCallback(bullet.btGhostPairCallback())
        self.physSolver = bullet.btSequentialImpulseConstraintSolver() 
        self.physWorld = bullet.btDiscreteDynamicsWorld(self.physDispatcher, self.physBroadphase, self.physSolver, self.physCollisionConfiguration)
        self.physWorld.setGravity(bullet.btVector3(0, 0, -15))

        # self.cells = {}
        self.entities = {}
    
    def updateWorld(self, dt):
        self.physWorld.stepSimulation(dt)
        
        dispatcher = self.physWorld.getDispatcher()
        manifolds = [dispatcher.getManifoldByIndexInternal(i) for i in xrange(dispatcher.getNumManifolds())]
        
        for mnf in manifolds:
            ent1 = mnf.getBody0().getUserPointer()['parent']
            ent2 = mnf.getBody1().getUserPointer()['parent']
            
            ent1.sendEntityEvent("collided", ent2)
            ent1.triggerOutput("OnCollide")
            ent2.sendEntityEvent("collided", ent1)
            ent2.triggerOutput("OnCollide")

        # for cell in self.cells.itervalues():
        #     cell.simulate()

        for entity in self.entities.itervalues():
            entity.simulate(dt)

    def addEntity(self, entity):
        if entity.name in self.entities:
            raise ValueError("This entity (or one with the same name) already exists in this world.")
        self.entities[entity.name] = entity

    def killEntity(self, entity):
        if entity.name not in self.entities:
            raise ValueError("This entity does not exist in this world")
        self.entities[entity.name] = None
    
    # def addCell(self, cell):
    #     self.cells[cell.name] = cell
    
    # def getCell(self, name):
    #     return self.cells[name]
    
    # def getCellNeighbours(self, name):
    #     return self.cells[name].getNeighbours()

    # @property
    # def root(self):
    #     return self.cells['root']

    # @classmethod
    # def makeWorld(cls, app):
    #     world = cls(app)
    #     cellMap = []
    #     for y, row in enumerate(cls.cellMap):
    #         cellRow = []
    #         cellMap.append(cellRow)
    #         for x, cellClass in enumerate(row):
    #             cell = cellClass(world, "cell %d:%d" % (x, y))
    #             cell.setPosition(x * cls.cellSize, y * cls.cellSize, 0)
    #             cellRow.append(cell)
    #     cls.assignNeighbours(cellMap)
    #     return world

    # @staticmethod
    # def assignNeighbours(cellMap):
    #     rows    = list(cellMap)
    #     columns = zip(*rows)

    #     # Cardinal directions: West and East
    #     for row in rows:
    #         for west, east in zip(*(row[n:] for n in xrange(2))):
    #             west.setNeighbour("e", east)
    #             east.setNeighbour("w", west)

    #     # Cardinal directions: North and South
    #     for col in columns:        
    #         for north, south in zip(*(col[n:] for n in xrange(2))):
    #             north.setNeighbour("s", south)
    #             south.setNeighbour("n", north)

    #     for offset in xrange(-len(columns), len(rows)):
    #         diag = list(diagonal(rows, offset))
    #         # Diagonals: Southeast and Northwest
    #         for northwest, southeast in zip(*(diag[n:] for n in xrange(2))):
    #             northwest.setNeighbour("se", southeast)
    #             southeast.setNeighbour("nw", northwest)

    #         # Diagonals: Southwest and Northeast
    #         diag = list(diagonal(reversed(rows), offset))
    #         for northeast, southwest in zip(*(diag[n:] for n in xrange(2))):
    #             northeast.setNeighbour("sw", southwest)
    #             southwest.setNeighbour("ne", northeast)



# class Cell(PhysicsEntity):
#     def __init__(self, world, name, model, tags=None, collisionModel=None, collisionTags=None, physGeom=None):
#         self._world = world
#         world.addCell(self)
#         self.neighbours = {}
#         self.entities   = {}
#         PhysicsEntity.__init__(self, self, name, model, "cell static terrain" + tags, collisionModel, collisionTags or "!static", physGeom)
#         # messenger.accept("change cell: [hero] '%s' [*]" % name, self.left)
#         # messenger.accept("change cell: [hero] [*] '%s'" % name, self.entered)
        
#     def setNeighbour(self, key, obj):
#         self.neighbours[key] = obj

#     def addEntity(self, ent):
#         if ent == self:
#             return
#         self._world.allEntities[ent.name] = ent
#         self.entities[ent.name] = ent
#         ent.model.reparentTo(self.model)
    
#     def simulate(self):
#         for ent in self.entities.itervalues():
#             ent.simulate()
    
#     # def show(self):
#     #     self.model.setAlphaScale(1)
#     #     for cell in self.neighbours.itervalues():
#     #         cell.model.setAlphaScale(0.75)

#     # def hide(self):
#     #     self.model.setAlphaScale(0.25)
#     #     for cell in self.neighbours.itervalues():
#     #         cell.model.setAlphaScale(0.25)
    
#     # def entered(self, _, __, ___):
#     #     self.show()
        
#     # def left(self, _, __, ___):
#     #     self.hide()
