
from ogre.physics import bullet

from supyrdupyr.entities import PhysicsEntity
from supyrdupyr.util import clamp

class Hero(PhysicsEntity):

    SPEED = 10
    JUMP_FORCE = 10
    MAX_SLOW_SPEED = 1000
    MAX_FAST_SPEED = 20000
    MAX_LOOK = 1000.0
    MOVE_KEYS = dict(w=(0, SPEED), s=(0, -SPEED), a=(-SPEED, 0), d=(SPEED, 0))
    MASS = 10

    hasGhostObject = True
    
    def __init__(self, cell, name, physShape, captureCamera=True):
        
        PhysicsEntity.__init__(self, cell, "Hero", self.createMesh(), self.MASS, "hero player", physShape=self.createPhysShape())

        self.physBody.setCollisionFlags(bullet.btCollisionObject.CF_CHARACTER_OBJECT)
        self.controller = bullet.btKinematicCharacterController(self.physBody, self.physShape, 0.35)
        
        self.captureCamera = captureCamera
        
        if captureCamera:
            self.setupCamera()
        
        self.canJump = False
        self.tasks = []
        self.currentMaxSpeed = self.MAX_SLOW_SPEED
    
    def createPhysShape(self):
        return bullet.btCapsuleShape(1.75, 1.75)

    def createMesh(self):
        return "testhero.mesh"
    
    def setupInput(self, messenger):
        for key, value in self.MOVE_KEYS.iteritems():
            self.app.messenger.accept(key, self.addTask, [self.move, value])
            self.app.messenger.accept(key+"-up", self.removeTask, [self.move, value])
        
        self.app.messenger.accept("space", self.jump)
        
        self.app.messenger.accept("shift", self.setMaxSpeed, [self.MAX_FAST_SPEED])
        self.app.messenger.accept("shift-up", self.setMaxSpeed, [self.MAX_SLOW_SPEED])

    def move(self, x, y):
        xform = self.physBody.getWorldTransform()
        strafeDir, upDir, forwardDir = xform.getBasis()
        strafeDir.normalize()
        upDir.normalize()
        forwardDir.normalize()
        
        walkDirection = bullet.btVector3(0, 0, 0)
        walkVelocity = self.currentMaxSpeed * 4.0
        walkDirection += strafeDir * x
        walkDirection += forwardDir * y
        
        self.controller.setWalkDirection(walkDirection)
    
    def setupCamera(self):
        self.app.messenger.accept("mouse-moved", self.panCamera)
        self.yAccum = 0
        self.cameraNode = self._model.createChildSceneNode()
        self.cameraNode.attachObject(self.app.camera)
        self.app.camera.setPosition((0, -10, 0))
        self.app.camera.lookAt(self._model)

    def setupCollisionEvents(self):
        self.app.messenger.accept("collided: [hero] [*]",    self.collidedWithAnything)
        self.app.messenger.accept("collided: [hero] [cell]", self.collidedWithCell)
    
    def collidedWithAnything(self, _, other):
        self.canJump = True
    
    def collidedWithCell(self, _, cell):
        self.cell = cell
    
    def setMaxSpeed(self, speed):
        self.currentMaxSpeed = speed

    def jump(self):
        if self.canJump:
            self.physBody.addRelForce(0, 0, 200)
            self.canJump = False

    def panCamera(self, input, evt):
        ms = input.mouseInput.getMouseState()
        #self.setRotation(self._model, , 0, 0)
        wt = self.physBody.getWorldTransform()
        y = wt.getEulerYPR()[0]
        wt.setEulerYPR(y + ms.X.rel * 0.2, 0, 0)
        
        self.yAccum = clamp(self.yAccum + ms.Y.rel * 0.2, 0, self.MAX_LOOK)
        self.cameraNode.pitch(0, self.yAccum / self.MAX_LOOK * 90 - 90, 0)
        self.app.camera.lookAt(self._model)
    
    def simulate(self):
        
        for func, args in self.tasks:
            func(*args)
        
        PhysicsEntity.simulate(self)

    def addTask(self, func, args):
        self.tasks.append((func, args))

    def removeTask(self, func, args):
        if (func, args) in self.tasks:
            self.tasks.remove((func, args))
        
    @property
    def location(self):
        return self.cell
