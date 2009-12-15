
import ogre.renderer.OGRE as ogre
from ogre.physics import bullet

from supyrdupyr.entities import PhysicsEntity
from supyrdupyr.util import clamp, multiplyVec3, multiplyQuat, dotMat3x3, getBasisAxes, matStr, vecStr
from math import radians

class Hero(PhysicsEntity):

    SPEED          = 5
    JUMP_FORCE     = 100000
    MAX_SLOW_SPEED = 1000
    MAX_FAST_SPEED = 10000
    MAX_LOOK       = 1000.0
    MOVE_FRICTION  = 0.9
    MOVE_KEYS = dict(w=(0, -SPEED, 0), s=(0, SPEED, 0), a=(SPEED, 0, 0), d=(-SPEED, 0, 0), q=(0, 0, -SPEED), e=(0, 0, SPEED))
    MASS = 10

    hasGhostObject = True
    physFlags      = bullet.btCollisionObject.CF_CHARACTER_OBJECT
    
    def __init__(self, world, captureCamera=True):
        
        super(Hero, self).__init__(world, "Hero", (0, 10, 0), self.createMesh(), "hero player", self.MASS, physShape=self.createPhysShape())
        
        self.controller = bullet.btKinematicCharacterController(self.physBody, self.physShape, 0.35)
        self.controller.setFallSpeed(2)
        self.world.physWorld.addAction(self.controller)
        self.walkDirection = bullet.btVector3(0, 0, 0)
        
        self.captureCamera = captureCamera
        
        if captureCamera:
            self.setupCamera()

        self.setupInput()
        
        self.canJump = False
        self.tasks = []
        self.maxSpeed        = self.MAX_SLOW_SPEED
        self.maxSpeedTarget  = self.MAX_SLOW_SPEED

        print "hero group:", bin(self.physBody.getBroadphaseHandle().m_collisionFilterGroup)
        print "hero mask:", bin(self.physBody.getBroadphaseHandle().m_collisionFilterMask)
    
    def createPhysShape(self):
        return bullet.btCapsuleShape(0.5, 0.5)

    def createMesh(self):
        return "testhero.mesh"
    
    def setupInput(self):
        for key, value in self.MOVE_KEYS.iteritems():
            self.app.messenger.accept(key, self.addTask, [self.move, value])
            self.app.messenger.accept(key+"-up", self.removeTask, [self.move, value])
        
        self.app.messenger.accept("space", self.jump)
        
        self.app.messenger.accept("shift", self.setMaxSpeed, [self.MAX_FAST_SPEED])
        self.app.messenger.accept("shift-up", self.setMaxSpeed, [self.MAX_SLOW_SPEED])

    def move(self, dt, x, y, r):
        wt = self.physBody.getWorldTransform()
        forwardDir, upDir, strafeDir = getBasisAxes(wt)
        
        self.walkDirection += multiplyVec3(forwardDir, x)
        self.walkDirection += multiplyVec3(strafeDir, y)
        
        rot = bullet.btQuaternion(bullet.btVector3(0, 1, 0), radians(r))
        orn = wt.getBasis()
        orn *= bullet.btMatrix3x3(rot)
        wt.setBasis(orn)
        self.physBody.setWorldTransform(wt)
    
    def setupCamera(self):
        self.app.messenger.accept("mouse-moved", self.mouseMoved)
        self.xAccum, self.yAccum, self.degree = 0, 0, 0
        #self.app.camera.setPosition(0, 20, 0)
        #self.app.camera.setAutoTracking(True, self.sceneNode)
        self.cameraNode = self.sceneNode.createChildSceneNode("MainCameraNode")
        #self.world.worldNode.createChildSceneNode("MainCameraNode")
        self.cameraNode.attachObject(self.app.camera)
        self.cameraNode.setPosition(0, 50, 0)
        self.cameraNode.pitch(ogre.Degree(-90))

    def setupEventHandlers(self):
        self.app.messenger.accept("collided: [hero] [*]",    self.collidedWithAnything)
        self.app.messenger.accept("collided: [hero] [terrain]", self.collidedWithTerrain)
    
    def collidedWithAnything(self, _, other):
        self.canJump = True

    def collidedWithTerrain(self, _, other):
        pass
    
    def setMaxSpeed(self, speed):
        self.maxSpeedTarget = speed

    def jump(self, _, __):
        if self.canJump:
            self.walkDirection += bullet.btVector3(0, self.JUMP_FORCE, 0)
            self.canJump = False

    def mouseMoved(self, input, evt):
        ms = input.mouseInput.getMouseState()
        wt = self.physBody.getWorldTransform()
        rot = bullet.btQuaternion(bullet.btVector3(0, 1, 0), radians(ms.X.rel))
        orn = wt.getBasis()
        orn *= bullet.btMatrix3x3(rot)
        wt.setBasis(orn)
        self.physBody.setWorldTransform(wt)
        self.cameraNode.roll(-radians(ms.X.rel))
        
        # self.yAccum = clamp(self.yAccum - ms.Y.rel, 0, self.MAX_LOOK)
        # degree = 90 - self.yAccum / self.MAX_LOOK * 90
        # self.cameraNode.pitch(ogre.Degree(degree - self.degree))
        # self.degree = degree
        # self.app.camera.lookAt(self.sceneNode.getPosition())
    
    def simulate(self, dt):
        self.maxSpeed += (self.maxSpeedTarget - self.maxSpeed) * 0.2
        self.walkDirection = multiplyVec3(self.walkDirection, self.MOVE_FRICTION)
        
        for func, args in self.tasks:
            func(dt, *args)
            
        wlen = self.walkDirection.length()
        if wlen > self.maxSpeed:
            self.walkDirection = multiplyVec3(self.walkDirection, self.maxSpeed / wlen)
        
        self.controller.setWalkDirection(multiplyVec3(self.walkDirection, dt))
        
        wt = self.physBody.getWorldTransform()
        origin, rotation = wt.getOrigin(), wt.getRotation()
        self.sceneNode.setPosition(origin.x(), origin.y(), origin.z())
        oren = ogre.Quaternion(rotation.w(), rotation.x(), rotation.y(), rotation.z())
        self.sceneNode.setOrientation(oren)
        #self.cameraNode.setOrientation(oren*-1)
        
        super(Hero, self).simulate(dt)

    def addTask(self, _, __, func, args):
        self.tasks.append((func, args))

    def removeTask(self, _, __, func, args):
        if (func, args) in self.tasks:
            self.tasks.remove((func, args))
        
    @property
    def location(self):
        return self.cell
