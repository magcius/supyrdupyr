from ogre.renderer import OGRE as ogre
from ogre.physics import bullet, OgreBulletC
import itertools

TAG_REGISTRY            = dict()

def getTagBits(tags):
    bits = 0
    notBits = False
    if not tags:
        return 0xFFFFFFFF
    
    if all(tag[0] == "!" for tag in tags):
        tags = [tag[1:] for tag in tags]
        notBits = True
        
    for tag in tags:
        if tag not in ("all", "*"):
            TAG_REGISTRY.setdefault(tag, len(TAG_REGISTRY))
            index = TAG_REGISTRY[tag]
            bits |= 1 << index
    
    if notBits:
        bits = ~bits
    
    return bits

class StaticEntity(object):
    
    # implements(IEntity)
    
    def __init__(self, cell, name, model, tags=None):
        self._inputs       = {}
        self._inputValues  = {}
        self._outputs      = {}
        self._outputValues = {}
        
        self._cell  = cell
        self._world = cell.world
        self._data  = None
        self._name  = name
        
        self.model  = model
        self.tags   = "all * " + tags
        
        self._cell.addEntity(self)
        
        self.app.messenger.accept("start use: [*] '%s'" % (self.name,), self.triggerOutput, extraArgs=[True, 'use'])
        self.app.messenger.accept("end use: [*] '%s'" % (self.name,), self.triggerOutput, extraArgs=[False, 'use'])

    def sendEntityEvent(self, eventtype, *entities, **kwargs):
        withTags = kwargs.get('withTags', True)
        permute  = kwargs.get('permute', False)
        loop = itertools.permutations(entities) if permute else [entities]
        for ents in loop:
            args = ((["'%s'" % ent.name] + (["[%s]" % tag for tag in ent.tags] if withTags else [])) for ent in ([self] + list(ents)))
            for eventargs in itertools.product(*args):
                self.app.messenger.send("%s: %s" % (eventtype, ' '.join(eventargs)), [self] + list(ents))
    
    @property
    def data(self):
        return self._data
    
    @data.setter
    def data(self, value):
        self._data = value

    @property
    def model(self):
        return self._model

    @model.setter
    def model(self, value):
        if isinstance(value, basestring):
            self._model = self.app.sceneManager.createEntity(self.name, value)
        else:
            self._model = value
            
        if self._cell == self:
            self.world.worldNode.attachNode(self._model)
        else:
            self._cell.model.attachNode(self._model)
    
    @property
    def name(self):
        return self._name
    
    @property
    def tags(self):
        return self._tags

    @tags.setter
    def tags(self, value):
        if isinstance(value, basestring):
            self._tags = value.split()
        else:
            self._tags = list(value)
        
    def setPosition(self, x, y, z):
        self._model.setPosition(ogre.Vector3(x, y, z))
    
    def setQuaternion(self, quat):
        self._model.setOrientation(quat)

    @property
    def world(self):
        return self._world

    @property
    def cell(self):
        return self._cell

    @property
    def app(self):
        return self._world.app

    @cell.setter
    def cell(self, value):
        if self._cell != value:
            self.sendEntityEvent("change cell", self._cell, value)
            del self._cell.entities[self.name]
            self._cell = value
            self._cell.addEntity(self)
    
    # Inputs/Outputs/Triggers
    
    def bindOutput(self, outputName, inputObj=None, inputName=None, func=None, args=None, filter=None):
        if inputObj is not None and inputName is not None:
            self._outputs[outputName] = (inputObj.triggerInput, [inputName], None)
        elif func is not None:
            self._outputs[outputName] = (func, args, filter)

    def bindInput(self, inputName, outputObj=None, outputName=None, func=None, args=None, filter=None):
        outputObj.bindOutput(inputName, self, outputName, func, args, filter)

    def bindInputHandler(self, inputName, func):
        self._inputs[inputName] = func
        
    def triggerOutput(self, value, outputName):
        if outputName in self._outputs:
            self._outputValues[outputName] = value
            func, args, filt = self._outputs[outputName]
            if callable(filt):
                value = filt(value)
            func(value, *tuple(args))

    def triggerInput(self, value, inputName):
        if inputName in self._inputs:
            self._inputValues[inputName] = value
            self._inputs[inputName](value)

    def getInput(self, inputName):
        try:
            return self._inputValues[inputName]
        except KeyError:
            return None

    def getOutput(self, outputName):
        try:
            return self._outputValues[outputName]
        except KeyError:
            return None
        
    def simulate(self):
        pass

class PhysicsEntityMotionState(bullet.btMotionState): 
    def __init__(self, entity, initialPosition):
        bullet.btMotionState.__init__(self)
        self.entity   = entity
        self.position = initialPosition
        self.rotation = bullet.btQuaternion()
        
    def getWorldTransform(self, worldTrans): 
        worldTrans.setOrigin(self.position.getOrigin())
        worldTrans.setBasis (self.position.getBasis())
        worldTrans.setRotation(self.rotation)
        
    def setWorldTransform(self, worldTrans):
        origin, rotation = worldTrans.getOrigin(), worldTrans.getRotation()
        self.entity.setPosition(origin.x(), origin.y(), origin.z())
        self.entity.setQuaternion(ogre.Quaternion(rotation.w(), rotation.x(), rotation.y(), rotation.z()))

class PhysicsEntity(StaticEntity):
    
    _physMass = None
    _physBody = None

    isKinematic    = False
    hasGhostObject = False
    MotionState    = PhysicsEntityMotionState
    
    def __init__(self, cell, name, model, mass, tags=None, collisionModel=None, collisionTags=None, physShape=None):
        StaticEntity.__init__(cell, name, model, tags)
        self.collisionTags  = collisionTags
        self.collisionModel = collisionModel
        self.physShape      = physShape
        self.physBody       = self.createBody(mass)

    def createBody(self, mass):

        if self.hasGhostObject:
            ghostObject =  bullet.btPairCachingGhostObject()
            ghostObject.setCollisionFlags(bullet.btCollisionObject.CF_CHARACTER_OBJECT)
            return ghostObject
        
        motionState = self.MotionState(self, bullet.btTransform(bullet.btQuaternion(0, 0, 0, 1), bullet.btVector3(0, 50, 0)))
        localInertia = bullet.btVector3(0, 0, 0)
        self._physShape.calculateLocalInertia(mass, localInertia)
        self._physMass = mass
        construct = bullet.btRigidBody.btRigidBodyConstructionInfo(mass, motionState, self._physShape, localInertia)
        body = bullet.btRigidBody(construct)
        if self.isKinematic:
            body.setCollisionFlags(body.getCollisionFlags() | bullet.btCollisionObject.CF_KINEMATIC_OBJECT)
        return body
    
    @property
    def collisionModel(self):
        return self._colModel

    @collisionModel.setter
    def collisionModel(self, value):
        if value is None:
            self._colModel = self._model
        else:
            if isinstance(value, basestring):
                self._colModel = self.app.sceneManager.createEntity(self.name+"-Collision", value)
            else:
                self.colModel = value
            self._model.attachNode(self._colModel)

    @property
    def physShape(self):
        return self._physShape

    @physShape.setter
    def physShape(self, value):
        if value is None:
            converter = OgreBulletC.StaticMeshToShapeConverter(self._colModel)
            self._physShape = converter.createTrimesh()
        else:
            self._physShape = value

        localInertia = bullet.btVector3(0, 0, 0)
        self._physShape.calculateLocalInertia(self._physMass, localInertia)
        
        if self._physBody is not None:
            self._physBody.setCollisionShape(self._physShape)
    
    @property
    def physBody(self):
        return self._physBody

    @physBody.setter
    def physBody(self, value):
        self._physBody = value
        if self._physMass is not None:
            self.physMass = self._physMass # reset on the new body
        self._physShape.setBody(self._physBody)
        self._world.physWorld.addRigidBody(self._physBody, getTagBits(self.tags), getTagBits(self.collisionTags))
        self._physBody.setUserPointer({"parent": self})

    @property
    def physMass(self):
        return self._physMass

    @physMass.setter
    def physMass(self, value):
        self._physMass = value
        localInertia = bullet.btVector3(0, 0, 0)
        self._physShape.calculateLocalInertia(value, localInertia)
        self._physBody.setMassProps(value, localInertia)
