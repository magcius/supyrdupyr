#            
#            Exploration Concept Demo
#            (c) magcius and mike 2009
#            
#            Notes here.
#            



import direct.directbase.DirectStart
from pandac.PandaModules import *
 
from direct.task import Task
from direct.actor import Actor
from direct.interval.IntervalGlobal import *
import math, sys

# Debug
#    0 - no debug info
#    1 - some data
#    2 - all data
#  When adding new things, general things should be 
#        if DEBUG == 1, specific or spammy should be
#        if DEBUG == 2

DEBUG = 2

# App class contains World class, no init parameters.
# *   handles input and passes it to World.
# *   handles graphics rendering.
# *   will handle sound output.
# *   currently has a Player hardcoded in.

# World class contains Player class along with entities
#            init: parent(App), Player(bool), model(Model),col_model(Model)
# *   handles game logic and object positions and movement
# *   takes player input information from App
# *   equates to one cell
# *   creating one with Player set to true will init a player
#                             and set the parent player to it

# Player class contains entity for graphics, logic for self
#            init: parent(World)
# *   handles position for self, logic for self
# *   can only belong to one World at one point.
# *   begins in the World that spawns it

SPEED     = 100

# base.cTrav = CollisionTraverser()

tasks = {}
geom_links = {}

def taskName(func, args):
    return "%s-%r-Task" % (func, args)

def addTask(func, *args):
    name = taskName(func, args)
    tasks[name] = taskMgr.add(func, name, extraArgs=args)

def removeTask(func, *args):
    taskMgr.remove(taskName(func, args))

def addGeomLink(geom, link):
    geom_links[geom.this] = link

def getGeomName(geom):
    return "foo"
    

class App(object):

    cell_list = { }
    
    def __init__(self):
        
        # env and envCollide are temporary
        # Once init'ed, use self.world.model and
        # self.world.col_model
        env = loader.loadModel("models/field2.egg")
        env.reparentTo(render)
        env.setScale(1, 1, 1)
        env.setPos(0, 0, 0)
        
        envCollide = loader.loadModel("models/field2.collision.egg")
        envCollide.reparentTo(env)
        envCollide.setScale(1, 1, 1)
        envCollide.setPos(0, 0, 0)

        # Setup our physics world
        self.odeWorld = OdeWorld()
        self.odeWorld.setGravity(0, 0, -9.81)
 
        # The surface table is needed for autoCollide
        self.odeWorld.initSurfaceTable(1)
        self.odeWorld.setSurfaceEntry(0, 0, 150, 0.0, 9.1, 0.9, 0.00001, 0.0, 0.002)
        
        self.space = OdeSimpleSpace()
        self.space.setCollisionEvent("collided")
        base.accept("collided", self.collided)
        self.space.setAutoCollideWorld(self.odeWorld)
        self.contactgroup = OdeJointGroup()
        self.space.setAutoCollideJointGroup(self.contactgroup)
        
        # base.disableMouse()
        
        self.world = World(self, create_player=True, model=env, col_model=envCollide)
        self.world.set_neighbours(self.world,"n")
        self.world.set_neighbours(self.world,"w")
        self.world.set_neighbours(self.world,"s")
        self.world.set_neighbours(self.world,"e")
        self.player = self.world.player
        #temp code to update neighbours once since there's no code
        #   for moving across cells
        #self.moved_to_new_cell()
                
        if DEBUG >= 1:
            print "Initialised application."

    def collided(self, entry):
        pass
    
    def moved_to_new_cell(self):
        for i in self.cell_list:
            self.cell_list[i].remove_node()
        self.cell_list = { }
        w = PandaNode("w")
        w = render.attachNewNode(w)
        if "w" in self.world.neighbours:
            self.world.neighbours["w"].model.copyTo(w)
            w.setPos(0, 512, 0)
        self.cell_list["w"] = w
        
        e = PandaNode("e")
        e = render.attachNewNode(e)
        if "e" in self.world.neighbours:
            self.world.neighbours["e"].model.copyTo(e)
            e.setPos(0, -512, 0)
        self.cell_list["e"] = e

        n = PandaNode("n")
        n = render.attachNewNode(n)
        if "n" in self.world.neighbours:
            self.world.neighbours["n"].model.copyTo(n)
            n.setPos(512, 0, 0)
        self.cell_list["n"] = n
        
        s = PandaNode("s")
        s = render.attachNewNode(s)
        if "s" in self.world.neighbours:
            self.world.neighbours["s"].model.copyTo(s)
            s.setPos(-512, 0, 0)
        self.cell_list["s"] = s

        for i in self.cell_list:
            self.cell_list[i].reparentTo(render)

        
        
    def simulate(self,task):
        self.space.autoCollide()
        self.odeWorld.quickStep(globalClock.getDt())
        
        self.player.simulate()

        x, y, z = self.player.actor.getPos()
        base.camera.setPos(x, y-10, z+2)

        self.contactgroup.empty()
        
        return Task.cont


class World(object):
    
    # Neighbours is a dictionary with cardinal directions.
    neighbours = { }
        
    def __init__(self, app, model, col_model, create_player=False):
        if DEBUG == 2:
            print ".Initialising world."
            
        self.app = app
        if create_player == True:
            self.player = Player(self)
            if DEBUG == 2:
                print "..Player created."
        
        self.neighbors = {}
        
        self.model = model
        self.col_model = col_model
        self.col_model.setName("world")

        self.trimesh = OdeTriMeshData(self.col_model, True)
        self.geom = OdeTriMeshGeom(self.app.space, self.trimesh)
        self.geom.setCategoryBits(BitMask32.allOn())
        self.geom.setCollideBits(BitMask32.allOn())
        addGeomLink(self.geom, self.col_model)
        
        if DEBUG >= 1:
            print ".World initialised."
    
    def set_neighbours(self, world, key):
        if DEBUG == 2:
            print ".Adding neighbour to world."
        self.neighbours[key] = world
            
class Player(object):
    
    def __init__(self, world):
        if DEBUG == 2:
            print "..Player initialising."
        self.world = world
        self.app   = world.app
        self.direction = 0
        # self.vx = 0
        # self.vy = 0
        # self.vz = 0
        self.actor = Actor.Actor("models/jeff.egg")
        self.actor.setName("jeff")
        self.actor.setScale(1, 1, 1)
        self.actor.setPos(0, 0, 500)
        self.actor.reparentTo(render)
        print self.actor.getName()
        
        base.accept("w", addTask, [self.accel, 0, SPEED])
        base.accept("w-up", removeTask, [self.accel, 0, SPEED])
        
        base.accept("s", addTask, [self.accel, 0, -SPEED])
        base.accept("s-up", removeTask, [self.accel, 0, -SPEED])
        
        base.accept("a", addTask, [self.accel, -SPEED, 0])
        base.accept("a-up", removeTask, [self.accel, -SPEED, 0])
        
        base.accept("d", addTask, [self.accel, SPEED, 0])
        base.accept("d-up", removeTask, [self.accel, SPEED, 0])

        base.accept("space", self.jump)

        base.accept("collision jeff world", self.collided)

        # cnodePath = self.actor.attachNewNode(CollisionNode('colNode'))
        # cnodePath.node().addSolid(CollisionRay(0, 0, 0, 0, 0, -1))
        # cnodePath.setZ(1)
        # cnodePath.show()
 
        # grav = self.gravity = CollisionHandlerGravity()
        # grav.setGravity(20)
        # grav.setOffset(0.1)
        # grav.addCollider(cnodePath, self.actor)
        # base.cTrav.addCollider(cnodePath, grav)
        # base.cTrav.showCollisions(render)

        self.collideBody = OdeBody(self.app.odeWorld)
        self.collideMass = OdeMass()
        self.collideMass.setCylinder(density=10, direction=3, radius=0.125, length=2)
        self.collideBody.setMass(self.collideMass)
        self.collideBody.setPosition(self.actor.getPos(render))
        self.collideBody.setQuaternion(self.actor.getQuat(render))
        self.collideGeom = OdeCylinderGeom(self.app.space, 0.125, 2)
        self.collideGeom.setCategoryBits(BitMask32(0x1))
        self.collideGeom.setCollideBits(BitMask32.allOn())
        self.collideGeom.setBody(self.collideBody)
        self.collideBody.setData(self.actor)

        addGeomLink(self.collideGeom, self.actor)
        
        if DEBUG >= 1:
            print "..Player initalised."

    def collided(self):
        print "COLLIDED WITH WORLD!"
            
    def accel(self, x=0, y=0, z=0):
        self.collideBody.addForce(x, y, z)
        return Task.cont

    def jump(self):
        if self.gravity.hasContact():
            self.accel(z=50)
        return Task.done
        
    def simulate(self):
        self.collideBody.setRotation(Mat3.identMat())
        self.actor.setPosQuat(render, self.collideBody.getPosition(), Quat(self.collideBody.getQuaternion()))
        # self.vz -= GRAVITY
        # self.vx *= FRICTION
        # self.vy *= FRICTION
        # self.vz *= AIR_DRAG

        # if self.vx > MAX_SPEED:
        #     self.vx = MAX_SPEED
        # elif self.vx < -MAX_SPEED:
        #     self.vx = -MAX_SPEED

        # if self.vy > MAX_SPEED:
        #     self.vy = MAX_SPEED
        # elif self.vy < -MAX_SPEED:
        #     self.vy = -MAX_SPEED

        # x, y, z = self.actor.getPos()
        # self.actor.setPos(x + self.vx * globalClock.getDt(),
        #                   y + self.vy * globalClock.getDt(),
        #                   z + self.vz * globalClock.getDt())

if __name__ == '__main__':
    app = App()
    
    #stuff here
    taskMgr.add(app.simulate, "SimulateTask")
    
    run()
