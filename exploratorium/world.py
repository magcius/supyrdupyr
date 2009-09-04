
from pandac.PandaModules import OdeWorld, OdeSimpleSpace, OdeJointGroup
from exploratorium.entities import CollidableEntity, geomToEnt
from exploratorium.util import diagonal

CELL_SIZE = 512

class World(object):

    def __init__(self):
        self.physWorld = OdeWorld()
        self.physWorld.setGravity(0, 0, -9.81)
        
        self.physWorld.initSurfaceTable(1)
        self.physWorld.setSurfaceEntry(0, 0, 150, 0.0, 9.1, 0.9, 0.00001, 0.0, 0.002)
        
        self.physSpace = OdeSimpleSpace()
        self.physContactGroup = OdeJointGroup()

        self.physSpace.setCollisionEvent("internal: collided")
        base.accept("internal: collided", self._collided)
        base.accept("enter frame", self._updateWorld)
        self.physSpace.setAutoCollideWorld(self.physWorld)
        self.physSpace.setAutoCollideJointGroup(self.physContactGroup)
        
        self.cellList = {}
        self.allEntities = {}

    def _collided(self, collision):
        ent1 = geomToEnt[collision.getGeom1()]
        ent2 = geomToEnt[collision.getGeom2()]
        messenger.send("collided: '%s' '%s'" % (ent1.name, ent2.name))
        messenger.send("collided: '%s' '%s'" % (ent2.name, ent1.name))

        for tag in ent1.tags:
            for tag2 in ent2.tags:
                messenger.send("collided: [%s] [%s]" % (tag, tag2), [ent1, ent2])
                messenger.send("collided: [%s] [%s]" % (tag2, tag), [ent2, ent1])
                
            messenger.send("collided: [%s] '%s'" % (tag, ent2.name), [ent1, ent2])
            messenger.send("collided: '%s' [%s]" % (ent2.name, tag), [ent2, ent1])

        for tag in ent2.tags:
            messenger.send("collided: [%s] '%s'" % (tag, ent1.name), [ent2, ent1])
            messenger.send("collided: '%s' [%s]" % (ent1.name, tag), [ent1, ent2])

    def _updateWorld(self):
        self.physSpace.autoCollide()
        self.physWorld.quickStep(globalClock.getDt())

        for cell in self.cells:
            cell.simulate()

        self.contactgroup.empty()
    
    def addCell(self, cell):
        self.cellList[cell.name] = cell
        cell.model.reparentTo(render)
    
    def getCell(self, name):
        return self.cellList[name]
    
    def getCellNeighbours(self, name):
        return self.cellList[name].getNeighbours()

    @property
    def root(self):
        return self.cellList['root']

class Cell(CollidableEntity):
    def __init__(self, world, name, model, kind=None, collisionModel=None, physGeom=None):
        self._world = world
        self.neighbours = {}
        self.entities   = {}
        CollidableEntity.__init__(self, self, name, model, "cell static terrain %s" % (kind,), collisionModel, physGeom)
        
    def setNeighbour(self, key, obj):
        self.neighbours[key] = obj

    def addEntity(self, ent):
        if ent == self:
            return
        self._world.allEntities[ent.name] = ent
        self.entities[ent.name] = ent
        ent.model.reparentTo(self._model)
    
    def simulate(self):
        for ent in self.entities:
            ent.simulate()


def makeWorld(cellMap):
    w = World()
    L = []
    for y, row in enumerate(cellMap):
        t = []
        L.append(t)
        for x, i in enumerate(row):
            if isinstance(i, tuple):
                cell = i[0](w, "root")
            else:
                cell = i(w, "cell %d:%d" % (x, y))
            cell.setPosition(x * CELL_SIZE, y * CELL_SIZE, 0)
            w.addCell(cell)
            t.append(cell)
    assignNeighbours(L)
    return w
    

def assignNeighbours(cellMap):
    rows    = list(cellMap)
    columns = zip(*rows)

    # Cardinal directions: West and East
    for row in rows:
        for west, east in zip(*(row[n:] for n in xrange(2))):
            west.setNeighbour("e", east)
            east.setNeighbour("w", west)

    # Cardinal directions: North and South
    for col in columns:        
        for north, south in zip(*(col[n:] for n in xrange(2))):
            north.setNeighbour("s", south)
            south.setNeighbour("n", north)
    
    for offset in xrange(-len(columns), len(rows)):
        diag = list(diagonal(rows, offset))
        for northwest, southeast in zip(*(diag[n:] for n in xrange(2))):
            northwest.setNeighbour("se", southeast)
            southeast.setNeighbour("nw", northwest)

        diag = list(diagonal(reversed(rows), offset))
        for northeast, southwest in zip(*(diag[n:] for n in xrange(2))):
            northeast.setNeighbour("sw", southwest)
            southwest.setNeighbour("ne", northeast)

from exploratorium.levels.root import DevCell

d = DevCell

world = makeWorld(
[[d, d,    d],
 [d, (d,), d],
 [d, d,    d]]
)
