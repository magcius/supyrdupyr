
from pandac.PandaModules import OdeWorld, OdeSimpleSpace, OdeJointGroup, OdeUtil
from exploratorium.entities import CollidableEntity, geomToEnt
from exploratorium.util import diagonal, geomId

class World(object):

    def __init__(self):
        self.physAccum = 0
        self.physStep  = 1. / 60
        
        self.physWorld = OdeWorld()
        self.physWorld.setGravity(0, 0, -15)
        
        self.physWorld.initSurfaceTable(1)
        self.physWorld.setSurfaceEntry(0, 0, 1, 0.0, 0, 0.9, 0.00001, 0.0, 1)
        
        self.physSpace = OdeSimpleSpace()
        self.physContactGroup = OdeJointGroup()

        self.physSpace.setCollisionEvent("internal: collided")
        base.accept("internal: collided", self._collided)
        base.accept("enter frame", self._updateWorld)
        self.physSpace.setAutoCollideWorld(self.physWorld)
        self.physSpace.setAutoCollideJointGroup(self.physContactGroup)
        
        self.cells = {}
        self.allEntities = {}

    def _collided(self, collision):
        ent1 = geomToEnt[geomId(collision.getGeom1())]
        ent2 = geomToEnt[geomId(collision.getGeom2())]
        ent1.sendEntityEvent("collided", ent2)
        ent2.sendEntityEvent("collided", ent1)
    
    def _updateWorld(self):

        dt = globalClock.getDt()
        self.physAccum += dt
        
        #while self.physAccum > self.physStep:
        self.physSpace.autoCollide()
        self.physWorld.quickStep(self.physStep)
        self.physContactGroup.empty()

        for cell in self.cells.itervalues():
            cell.simulate()
    
    def addCell(self, cell):
        self.cells[cell.name] = cell
        cell.model.reparentTo(render)
    
    def getCell(self, name):
        return self.cells[name]
    
    def getCellNeighbours(self, name):
        return self.cells[name].getNeighbours()

    @property
    def root(self):
        return self.cells['root']

class Cell(CollidableEntity):
    def __init__(self, world, name, model, tags=None, collisionModel=None, collisionTags=None, physGeom=None):
        self._world = world
        self.neighbours = {}
        self.entities   = {}
        CollidableEntity.__init__(self, self, name, model, "cell static terrain" + tags, collisionModel, collisionTags or "!static", physGeom)
        base.accept("change cell: [hero] '%s' [*]" % name, self.left)
        base.accept("change cell: [hero] [*] '%s'" % name, self.entered)
        self._model.setTransparency(1)
        self._model.clearColor()
        
    def setNeighbour(self, key, obj):
        self.neighbours[key] = obj

    def addEntity(self, ent):
        if ent == self:
            return
        self._world.allEntities[ent.name] = ent
        self.entities[ent.name] = ent
        ent.model.reparentTo(self._model)
    
    def simulate(self):
        for ent in self.entities.itervalues():
            ent.simulate()

    def show(self):
        self._model.setAlphaScale(1)
        for cell in self.neighbours.itervalues():
            cell.model.setAlphaScale(0.75)

    def hide(self):
        self._model.setAlphaScale(0.25)
        for cell in self.neighbours.itervalues():
            cell.model.setAlphaScale(0.25)
    
    def entered(self, otherCell):
        self.show()

    def left(self, otherCell):
        self.hide()

def makeWorld(cellMap, cellSize=512):
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
            cell.setPosition(x * cellSize, y * cellSize, 0)
            cell.hide()
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

    print "END OF assignNeighbours"

from exploratorium.levels.root import DevCell

d = DevCell

world = makeWorld(
[[d, d, d, d],
 [d, d, d, d],
 [d, d, d, d],
 [d, d, d, (d,)]]
)
