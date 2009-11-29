from panda3d.core import Mat3
from panda3d.ode import OdeMass, OdeCylinderGeom, OdeRayGeom
from exploratorium.entities import PhysicsEntity
from exploratorium.util import clamp

# from math import sin, cos, pi

SPEED = 10
JUMP_FORCE = 10
MAX_SLOW_SPEED = 1000
MAX_FAST_SPEED = 20000
MAX_LOOK = 1000.

class Hero(PhysicsEntity):
    
    def __init__(self, cell, captureCamera=True):
        
        PhysicsEntity.__init__(self, cell, "hero", "jeff.egg", 10, "physics hero")

        self.physGeom = OdeCylinderGeom(self._world.physSpace, 0.125, 2)
        self.useRay = OdeRayGeom(self._world.physSpace, 50)
        bounds = self._model.getBounds()
        # self._model.setColor(0, 0, 0)
        
        base.accept("collided: [hero] [*]",    self._collidedWithAnything)
        base.accept("collided: [hero] [cell]", self._collidedWithCell)

        KEYS = dict(w=(0, SPEED), s=(0, -SPEED), a=(-SPEED, 0), d=(SPEED, 0))
        for key in KEYS:
            base.accept(key, self.addTask, [self.move, KEYS[key]])
            base.accept(key+"-up", self.removeTask, [self.move, KEYS[key]])
        
        base.accept("space", self.jump)
        
        base.accept("shift", self.setMaxSpeed, [MAX_FAST_SPEED])
        base.accept("shift-up", self.setMaxSpeed, [MAX_SLOW_SPEED])

        self.captureCamera = captureCamera
        
        if captureCamera:
            base.camera_root = self._model.attachNewNode("camera_root")
            base.camera.reparentTo(base.camera_root)
            base.camera.setPos(0, -10, 0)
            base.camera.lookAt(self._model)
            base.oldx, base.oldy, base.yaccum = 0, 0, 0
        
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
            self.physBody.addRelForce(0, 0, 200)
            self.canJump = False

    def simulate(self):
        
        self.physBody.setAngularVel(0, 0, 0)
        self.physBody.setQuaternion(self._model.getQuat())
        
        x, y, z = self.physBody.getLinearVel()
        speed = x*x + y*y
        if speed > self.currentMaxSpeed:
            frac = self.currentMaxSpeed / speed
            self.physBody.setLinearVel(x*frac, y*frac, z)
        
        for func, args in self.tasks:
            func(*args)

        if self.captureCamera:
            mp = base.win.getPointer(0)
            x, y = mp.getX(), mp.getY()
            self.setRotation(self._model, x - base.oldx, 0, 0)
            base.yaccum = clamp(base.yaccum + y - base.oldy, 0, MAX_LOOK)
            # ratio = base.yaccum / MAX_LOOK * pi/2
            # cy, cz = sin(ratio) * -10, cos(ratio) * 5
            base.camera_root.setHpr(0, base.yaccum / MAX_LOOK * 90 - 90, 0)
            base.camera.lookAt(self._model)
            base.oldx, base.oldy = x, y

        self.useRay.setQuaternion(self._model.getQuat())
        self.useRay.setPosition(self._model.getPos())
        
        PhysicsEntity.simulate(self)

    def addTask(self, func, args):
        self.tasks.append((func, args))

    def removeTask(self, func, args):
        if (func, args) in self.tasks:
            self.tasks.remove((func, args))
        
    @property
    def location(self):
        return self.cell
