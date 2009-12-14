
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


class BaseEntity(object):
    def __init__(self, world, name, tags=""):
        self.world = world
        self.world.addEntity(self)
        self.tags   = "all * " + tags
        self.name = name
        self.data = None
        
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
    def app(self):
        return self.world.app
    
    def simulate(self, dt):
        pass

class InputOutputMeta(type):
    def __new__(cls, names, bases, dct):
        def formatSpec(spec):
            return '\n'.join(formatPutSpec(s) for s in spec.iteritems())
        
        def formatPutSpec(spec):
            name, (parameters, doc) = spec
            return "    %s : %s\n      %s\n" % (name, ' '.join("<%s>" % (type.__name__,) for type in (parameters or [])) or "none", doc)
        
        D = dct.copy()
        D.update(dict(outputSpec={}, inputSpec={}))
        for base in reversed(bases):
            if hasattr(base, "outputSpec"):
                D["outputSpec"].update(getattr(base, "outputSpec"))
            if hasattr(base, "inputSpec"):
                D["inputSpec"].update(getattr(base, "inputSpec"))
            if hasattr(base, "inputHandlers"):
                D["inputHanders"].update(getattr(base, "inputHandlers"))
        
        D["outputSpec"].update(dct.get("outputSpec", {}))
        D["inputSpec"].update(dct.get("inputSpec", {}))
        D["inputHandlers"].update(dct.get("inputHandlers", {}))
        
        D.setdefault("__doc__", "")
        D["__doc__"] += \
"""

  Inputs for this entity:
%s

  Outputs for this entity:
%s
""" % (formatSpec(D["inputSpec"]), formatSpec(D["outputSpec"]))
        return type.__new__(cls, names, bases, D)

def checkSpec(spec, value):
    types, doc = spec
    return all(isinstance(VALUE, TYPE) for VALUE, TYPE in zip(value, types))

class LogicEntity(BaseEntity):
    
    """
    An entity that handles basic logic functions. The input/output system
    is modeled after the Source engine.
    """

    __metaclass__ = InputOutputMeta
    
    # Inputs/Outputs/Triggers
    
    def __init__(self, world, name, tags=""):
        super(LogicEntity, self).__init__(world, name, tags)
        
        self.isNotKilled = True # FIXME: remove from world
        self.enabled = True
        
        self._outputBindings = {}
        
        self.setupEventHandlers()
        self.setupIO()
    
    def sendEntityEvent(self, eventtype, *entities, **kwargs):
        withTags = kwargs.get('withTags', True)
        permute  = kwargs.get('permute', False)
        loop = itertools.permutations(entities) if permute else [entities]
        for ents in loop:
            args = ((["'%s'" % ent.name] + (["[%s]" % tag for tag in ent.tags] if withTags else [])) for ent in ([self] + list(ents)))
            for eventargs in itertools.product(*args):
                self.app.messenger.send("%s: %s" % (eventtype, ' '.join(eventargs)), [self] + list(ents))
    
    def kill(self, value):
        self.isNotKilled = False # FIXME: Instead of setting a flag, clear it off the "world"
        self.fireOutput("OnKill")

    def enable(self, value):
        self.enabled = True

    def disable(self, value):
        self.enabled = False

    def toggle(self, value):
        self.enabled = not self.enabled
    
    def setupEventHandlers(self):
        pass

    def setupIO(self):
        pass
    
    def bindOutput(self, outputName, inputObj, inputName):
        assert outputName in self.outputSpec
        self._outputBindings.setdefault(outputName, [])
        self._outputBindings[outputName].append((inputObj, inputName))
    
    def fireOutput(self, outputName, value=None):
        if self.isNotKilled and self.enabled:
            assert checkSpec(self.outputSpec[outputName], value)
            for inputObj, inputName in self._outputBindings.get(outputName, []):
                inputObj.triggerInput(inputName, value)

    def _fireOutput_event(self, _, __, outputName, value=None):
        self.fireOutput(value, outputName)
    
    def triggerInput(self, inputName, value):
        if self.isNotKilled:
            assert inputName in self.inputSpec and checkSpec(self.inputSpec[inputName], value)

            if inputName in self.inputHandlers:
                handler = self.inputHandlers[inputName]
                args = []
            
                if isinstance(handler, tuple):
                    handler, args = handler
                    
                if callable(handler):
                    handler(self, value + args)
                elif isinstance(handler, str):
                    self.fireOutput(handler, args)
    
    inputHandlers = {
        "Kill": kill,
        "Enable": enable,
        "Disable": disable,
        "Toggle": toggle,
    }
    
    inputSpec = {
        "Kill": (None, "Remove this entity from the game."),
        "Enable": (None, "Enable this entity."),
        "Disable": (None, "Disable this entity."),
        "FireUser1": (None, "User-defined input for all your other tasks."),
        "FireUser2": (None, "User-defined input for all your other tasks."),
        "FireUser3": (None, "User-defined input for all your other tasks."),
        "FireUser4": (None, "User-defined input for all your other tasks."),
    }

    outputSpec = {
        "OnKill": (None, "Fired when this entity is removed from the game."),
        "OnUser1": (None, "User-defined output for all your other tasks."),
        "OnUser2": (None, "User-defined output for all your other tasks."),
        "OnUser3": (None, "User-defined output for all your other tasks."),
        "OnUser4": (None, "User-defined output for all your other tasks."),
    }

class VisibleEntity(LogicEntity):

    """
    A visible entity that renders itself using the given model.
    """
    def __init__(self, world, name, position, model, tags=""):
        super(VisibleEntity, self).__init__(name, world, tags)
        
        self.model  = model
        self._model.setPosition(position)

    def setupEventHandlers(self):
        self.app.messenger.accept("start use: [*] '%s'" % (self.name,), self._fireOutput_event, extraArgs=['OnUse', True])
        self.app.messenger.accept("end use: [*] '%s'" % (self.name,), self._fireOutput_event, extraArgs=['OnUse', False])
        
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
    
    outputSpec = {
        "OnUse": (None, "Fired when a user fires this object."),
    }

    
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

class PhysicsEntity(VisibleEntity):
    
    _physMass = None
    _physBody = None
    
    MotionState = PhysicsEntityMotionState
    physFlags   = 0
    
    def __init__(self, cell, name, position, model, mass, tags="", collisionModel=None, collisionTags=None, physShape=None):
        super(PhysicsEntity, self).__init__(cell, name, model, position, "physics" + tags)
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
        self.world.physWorld.addRigidBody(self._physBody, getTagBits(self.tags), getTagBits(self.collisionTags))
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
        
    outputSpec = {
        "OnCollide": ([PhysicsEntity], "Fired when this object collides with another one."),
    }

class StaticEntity(PhysicsEntity):
    physFlags = bullet.btCollisionObject.CF_STATIC_OBJECT

class TriggerEntity(PhysicsEntity):
    physFlags = bullet.btCollisionObject.CF_NO_CONTACT_RESPONSE
    
    def setupIO(self):
        self.bindOutput("OnCollide", self, "Trigger")
        
    inputHandlers = {
        "Trigger": "OnTrigger",
    }
    
    inputSpec = {
        "Trigger": (None, "Fire the OnTrigger output."),
    }
    
    outputSpec = {
        "OnTrigger": (None, "Fired when this object is triggered."),
    }
