from panda3d.core import Mat3
from panda3d.ode import OdeMass, OdeCylinderGeom
from exploratorium.entities import PhysicsEntity

SPEED = 10
JUMP_FORCE = 10
MAX_SLOW_SPEED = 100
MAX_FAST_SPEED = 2000

class Hero(PhysicsEntity):
    
    def __init__(self, cell):
        
        PhysicsEntity.__init__(self, cell, "hero", "jeff.egg", 10, "physics hero")

        self.physGeom = OdeCylinderGeom(self._world.physSpace, 0.125, 2)
        self._model.setColor(0, 0, 0)
        
        base.accept("collided: [hero] [*]",    self._collidedWithAnything)
        base.accept("collided: [hero] [cell]", self._collidedWithCell)

        base.accept("w", self.addTask, [self.move, 0, SPEED])
        base.accept("w-up", self.removeTask, [self.move, 0, SPEED])
        
        base.accept("s", self.addTask, [self.move, 0, -SPEED])
        base.accept("s-up", self.removeTask, [self.move, 0, -SPEED])
        
        base.accept("a", self.addTask, [self.move, -SPEED, 0])
        base.accept("a-up", self.removeTask, [self.move, -SPEED, 0])
        
        base.accept("d", self.addTask, [self.move, SPEED, 0])
        base.accept("d-up", self.removeTask, [self.move, SPEED, 0])

        base.accept("space", self.jump)

        base.accept("shift", self.setMaxSpeed, [MAX_FAST_SPEED])
        base.accept("shift-up", self.setMaxSpeed, [MAX_SLOW_SPEED])
        
        self.canJump = False
        self.tasks = []
        self.currentMaxSpeed = MAX_SLOW_SPEED
    
    def _collidedWithAnything(self, _, other):
        self.canJump = True
    
    def _collidedWithCell(self, _, cell):
        self.cell = cell
    
    def setMaxSpeed(self, speed):
        self.currentMaxSpeed = speed
        
    def move(self, x, y):
        self.physBody.addRelForce(x, y, 0)

    def jump(self):
        if self.canJump:
            print "Jumping!"
            self.physBody.addRelForce(0, 0, 200)
            self.canJump = False

    def simulate(self):
        self._model.setHpr(0, 0, 0)
        
        self.physBody.setAngularVel(0, 0, 0)
        self.physBody.setQuaternion(self._model.getQuat())
        
        x, y, z = self.physBody.getLinearVel()
        speed = x*x + y*y
        if speed > self.currentMaxSpeed:
            frac = self.currentMaxSpeed / speed
            self.physBody.setLinearVel(x*frac, y*frac, z)
        
        for func, args in self.tasks:
            func(*args)
            
        x, y, z = self.physBody.getPosition()
        base.camera.setPos(x, y+10, z+2)
        base.camera.lookAt(x, y, z)
        
        PhysicsEntity.simulate(self)

    def addTask(self, func, *args):
        self.tasks.append((func, args))

    def removeTask(self, func, *args):
        if (func, args) in self.tasks:
            self.tasks.remove((func, args))
        
    @property
    def location(self):
        return self.cell
