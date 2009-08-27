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
#            init: parent(App), Player(bool)
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

SPEED     = 1
FRICTION  = 0.98
AIR_DRAG  = 0.90
MAX_SPEED = 10

base.cTrav = CollisionTraverser()

tasks = {}

def taskName(func, args):
    return "%s-%r-Task" % (func, args)

def addTask(func, *args):
    name = taskName(func, args)
    tasks[name] = taskMgr.add(func, name, extraArgs=args)

def removeTask(func, *args):
    taskMgr.remove(taskName(func, args))


class App(object):
    
    def __init__(self):
        if DEBUG >= 1:
            print "Initialising application."
        self.world = World(self, create_player=True)
        self.player = self.world.player
        
        
        #temporary model until Worlds are finished
        self.env = loader.loadModel("models/field2.egg")
        self.env.reparentTo(render)
        self.env.setScale(1, 1, 1)
        self.env.setPos(0, 0, 0)

        self.envCollide = loader.loadModel("models/field2.collision.egg")
        self.envCollide.reparentTo(self.env)
        self.envCollide.setScale(1, 1, 1)
        self.envCollide.setPos(0, 0, 0)
        self.envCollide.setCollideMask(BitMask32.allOn())
        

        # base.disableMouse()
        
        # base.camera.setPos(self.player.x,self.player.y-10,self.player.z + 2)
        ##not set to point at the player yet, direction static
        
        if DEBUG >= 1:
            print "Initialised application."
    
    def simulate(self,task):
        ##debug movement to test.
        #self.player.x -= 0.05
        #self.player.y += 0.009
        self.player.simulate()

        x, y, z = self.player.actor.getPos()
        base.camera.setPos(x, y-10, z+2)
        
        return Task.cont


class World(object):
    
    def __init__(self, parent, create_player=False):
        if DEBUG == 2:
            print ".Initialising world."
        self.parent = parent
        if create_player == True:
            self.player = Player(self)
            if DEBUG == 2:
                print "..Player created."
        if DEBUG >= 1:
            print ".World initialised."
            
class Player(object):
    
    def __init__(self,parent):
        if DEBUG == 2:
            print "..Player initialising."
        self.parent = parent
        self.direction = 0
        self.vx = 0
        self.vy = 0
        self.vz = 0
        self.actor = Actor.Actor("models/jeff.egg")
        self.actor.setScale(1, 1, 1)
        self.actor.setPos(0, 0, 10)
        self.actor.reparentTo(render)
        
        base.accept("w", addTask, [self.accel, 0, SPEED])
        base.accept("w-up", removeTask, [self.accel, 0, SPEED])
        
        base.accept("s", addTask, [self.accel, 0, -SPEED])
        base.accept("s-up", removeTask, [self.accel, 0, -SPEED])
        
        base.accept("a", addTask, [self.accel, -SPEED, 0])
        base.accept("a-up", removeTask, [self.accel, -SPEED, 0])
        
        base.accept("d", addTask, [self.accel, SPEED, 0])
        base.accept("d-up", removeTask, [self.accel, SPEED, 0])

        base.accept("space", self.jump)

        cnodePath = self.actor.attachNewNode(CollisionNode('colNode'))
        cnodePath.node().addSolid(CollisionRay(0, 0, 0, 0, 0, -1))
        cnodePath.setZ(1)
        cnodePath.show()
 
        grav = self.gravity = CollisionHandlerGravity()
        grav.setGravity(20)
        grav.setOffset(0.1)
        grav.addCollider(cnodePath, self.actor)
        base.cTrav.addCollider(cnodePath, grav)
        base.cTrav.showCollisions(render)
        
        if DEBUG >= 1:
            print "..Player initalised."

    def accel(self, x=0, y=0, z=0):
        self.vx += x
        self.vy += y
        self.vz += z

        return Task.cont

    def jump(self):
        if self.gravity.hasContact():
            self.accel(z=50)
        
    def simulate(self):
        # self.vz -= GRAVITY
        self.vx *= FRICTION
        self.vy *= FRICTION
        self.vz *= AIR_DRAG

        if self.vx > MAX_SPEED:
            self.vx = MAX_SPEED
        elif self.vx < -MAX_SPEED:
            self.vx = -MAX_SPEED

        if self.vy > MAX_SPEED:
            self.vy = MAX_SPEED
        elif self.vy < -MAX_SPEED:
            self.vy = -MAX_SPEED

        x, y, z = self.actor.getPos()
        self.actor.setPos(x + self.vx * globalClock.getDt(),
                          y + self.vy * globalClock.getDt(),
                          z + self.vz * globalClock.getDt())

if __name__ == '__main__':
    app = App()
    
    #stuff here
    taskMgr.add(app.simulate, "SimulateTask")
    
    run()
    
    
