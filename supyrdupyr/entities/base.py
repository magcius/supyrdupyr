
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

class InputOutputMeta(type):
    def __new__(cls, names, bases, dct):
        def formatSpec(spec):
            return '\n'.join(formatPutSpec(s) for spec in spec.iteritems())
        
        def formatPutSpec(spec):
            name, (parameters, doc) = spec
            return "    %s : %s\n      %s\n" % (name, ' '.join("<%s>" % (type,) for type in (parameters or [])) or "none", doc)
        
        dct.setdefault("outputSpec", {})
        dct.setdefault("inputSpec", {})
        for base in bases:
            if hasattr(base, "outputSpec"):
                dct["outputSpec"].update(getattr(base, "outputSpec"))
            if hasattr(base, "inputSpec"):
                dct["inputSpec"].update(getattr(base, "outputSpec"))

        dct["__doc__"] += \
"""

  Inputs for this various entity:
%s

  Outputs for this various entity:
%s
""" % (formatSpec(dct["inputSpec"]), formatSpec(dct["outputSpec"]))
        return type.__new__(cls, names, bases, dct)

class BaseEntity(object):
    def __init__(self, world, name, tags=""):
        self.world = world
        self.world.addEntity(self)
        self.tags   = "all * " + tags
    
class LogicEntity(BaseEntity):
    
    """
    An entity that handles basic logic functions. The input/output system
    is modeled after the Source engine.
    """

    __metaclass__ = InputOutputMeta
    
    # Inputs/Outputs/Triggers
    
    def __init__(self, world, name, tags=""):
        self.world = world
        self.world.addEntity(self)
        
        self.enabled = True
        
        self._outputBindings = {}
        
        self.setupEventHandlers()
        self.setupIO()

    @property
    def name(self):
        return self._name
    
    def sendEntityEvent(self, eventtype, *entities, **kwargs):
        withTags = kwargs.get('withTags', True)
        permute  = kwargs.get('permute', False)
        loop = itertools.permutations(entities) if permute else [entities]
        for ents in loop:
            args = ((["'%s'" % ent.name] + (["[%s]" % tag for tag in ent.tags] if withTags else [])) for ent in ([self] + list(ents)))
            for eventargs in itertools.product(*args):
                self.app.messenger.send("%s: %s" % (eventtype, ' '.join(eventargs)), [self] + list(ents))
    
    def kill(self):
        self.enabled = False # FIXME: Instead of setting a flag, clear it off the "world"
        self.fireOutput("OnKill")
        
    def setupIO(self):
        pass
    
    def setupEventHandlers(self):
        pass
    
    def bindOutput(self, outputName, inputObj, inputName, args=None, kwargs=None):
        assert outputName in self.outputSpec
        self._outputBindings.setdefault(outputName, [])
        self._outputBindings[outputName].append((inputObj, inputName, args or [], kwargs or {}))
        
    def fireOutput(self, value, outputName):
        if self.enabled:
            for inputObj, inputName, args, kwargs in self._outputBindings.get(outputName, []):
                inputObj._triggerInput(value, inputName, args, kwargs)

    def _fireOutput_event(self, _, __, value, outputName):
        self.fireOutput(value, outputName)
    
    def _triggerInput(self, value, inputName, args, kwargs):
        if self.enabled:
            assert inputName in self.inputSpec
            func = self.inputHandlers[inputName]
            func(self, value, *args, **kwargs)

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

    @property
    def tags(self):
        return self._tags
    
    @tags.setter
    def tags(self, value):
        if isinstance(value, basestring):
            self._tags = value.split()
        else:
            self._tags = list(value)
    
    @property
    def data(self):
        return self._data
    
    @data.setter
    def data(self, value):
        self._data = value

    inputHandlers = {
        "Kill": kill,
    }
    
    inputSpec = {
        "Kill": (None, "Remove this entity from the game.")
    }

    outputSpec = {
        "OnKill": (None, "Fired when this entity is removed from the game."),
    }

class VisibleEntity(LogicEntity):

    """
    A visible entity that renders itself using the given model.
    """
    def __init__(self, world, name, position, model, tags=""):

        LogicEntity.__init__(self, name, world, tags)
        
        self._data  = None
        self._name  = name
        
        self.model  = model
        self._model.setPosition(position)

    def setupEventHandlers(self):
        self.app.messenger.accept("start use: [*] '%s'" % (self.name,), self._fireOutput_event, extraArgs=[True, 'OnTrigger'])
        self.app.messenger.accept("end use: [*] '%s'" % (self.name,), self._fireOutput_event, extraArgs=[False, 'OnTrigger'])
        self.app.messenger.accept("collided: '%s' [cell]" % name, self.changeCells)
    
    @property
    def model(self):
        return self._model

    @model.setter
    def model(self, value):
        if isinstance(value, basestring):
            self._model = self.app.sceneManager.createEntity(self.name, value)
        else:
            self._model = value
        
        self.world.worldNode.attachNode(self._model)
    
    @property
    def world(self):
        return self._world
    
    @property
    def app(self):
        return self._world.app
    
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

class PhysicsEntity(EntityBase):
    
    _physMass = None
    _physBody = None
    
    MotionState = PhysicsEntityMotionState
    physFlags   = 0
    
    def __init__(self, cell, name, position, model, mass, tags="", collisionModel=None, collisionTags=None, physShape=None):
        EntityBase.__init__(cell, name, model, position, "physics" + tags)
        self.collisionTags  = collisionTags
        self.collisionModel = collisionModel
        self.physShape      = physShape
        self.physBody       = self.createBody(mass, position)

    def createBody(self, mass, position):
        
        motionState = self.MotionState(self, bullet.btTransform(bullet.btQuaternion(0, 0, 0, 1), bullet.btVector3(position)))
        localInertia = bullet.btVector3(0, 0, 0)
        self._physShape.calculateLocalInertia(mass, localInertia)
        self._physMass = mass
        construct = bullet.btRigidBody.btRigidBodyConstructionInfo(mass, motionState, self._physShape, localInertia)
        body = bullet.btRigidBody(construct)
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
        self._physBody.setCollisionFlags(self._physBody.getCollisionFlags() | self.physFlags)

    @property
    def physMass(self):
        return self._physMass

    @physMass.setter
    def physMass(self, value):
        self._physMass = value
        localInertia = bullet.btVector3(0, 0, 0)
        self._physShape.calculateLocalInertia(value, localInertia)
        self._physBody.setMassProps(value, localInertia)

class StaticEntity(PhysicsEntity):
    physFlags = bullet.btCollisionObject.CF_STATIC_OBJECT

class TriggerEntity(PhysicsEntity):
    physFlags = bullet.btCollisionObject.CF_NO_COLLISION_RESPONSE

    def setupEventHandlers(self):
        pass
