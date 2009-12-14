
"""
Base entities.
"""

from ogre.renderer import OGRE as ogre
from ogre.physics import bullet, OgreBulletC
import itertools

TAG_REGISTRY            = dict()

def getTagBits(tags):
    """
    Get the collision and category bits for our tags.
    """
    bits = 0
    notBits = False
    if not tags:
        return 0xFF
    
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
    """
    A base entity. Has name, tags, world, apps and custom data. That's it.
    The name must be unique for each entity.
    """
    def __init__(self, world, name, tags=""):
        self.tags   = "all * " + tags
        self.name = name
        self.data = None
        self.world = world
        self.world.addEntity(self)
        
    @property
    def tags(self):
        """
        The entity tags used when sending global events.
        """
        return self._tags
    
    @tags.setter
    def tags(self, value):
        if isinstance(value, basestring):
            self._tags = value.split()
        else:
            self._tags = list(value)
    
    @property
    def app(self):
        """
        The application.
        """
        return self.world.app
    
    def simulate(self, dt):
        pass

    def sendEntityEvent(self, eventtype, *entities, **kwargs):
        """
        Send an entity event through the messenger.

        Example:

            hero.sendEntityEvent("collided", ground)

        will send:

            collided: 'heroName' 'groundName'
            collided: [*] 'groundName'
            collided: [hero] 'groundName'
            collided: [physics] 'groundName'
            etc.
        
        with the variables "hero" and "ground" being arguments.
        [] brackets represent a tag. '' quotes represent a name in the world.
        heroName and groundName represent the names of the hero and ground entities.
        """
        withTags = kwargs.get('withTags', True)
        permute  = kwargs.get('permute', False)
        loop = itertools.permutations(entities) if permute else [entities]
        for ents in loop:
            args = ((["'%s'" % ent.name] + (["[%s]" % tag for tag in ent.tags] if withTags else [])) for ent in ([self] + list(ents)))
            for eventargs in itertools.product(*args):
                self.app.messenger.send("%s: %s" % (eventtype, ' '.join(eventargs)), [self] + list(ents))

class InputOutputMeta(type):
    """
    Metaclass to implement the input/outputSpec and inputHandlers documentation and inheritance.
    """
    def __new__(cls, names, bases, dct):
        def formatSpec(spec):
            return '\n'.join(formatPutSpec(s) for s in spec.iteritems())
        
        def formatPutSpec(spec):
            name, (parameters, doc) = spec
            return "    %s : %s\n      %s\n" % (name, ' '.join("<%s>" % (type.__name__,) for type in (parameters or [])) or "none", doc)
        
        D = dct.copy()
        D.update(dict(outputSpec={}, inputSpec={}, inputHandlers={}))
        for base in reversed(bases):
            if hasattr(base, "outputSpec"):
                D["outputSpec"].update(getattr(base, "outputSpec"))
            if hasattr(base, "inputSpec"):
                D["inputSpec"].update(getattr(base, "inputSpec"))
            if hasattr(base, "inputHandlers"):
                D["inputHandlers"].update(getattr(base, "inputHandlers"))
        
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

# def checkSpec(spec, value):
#     """
#     Checks the spec to make sure it has the specific types.
#     """
#     types, doc = spec
#     return all(isinstance(VALUE, TYPE) for VALUE, TYPE in zip(value, types))

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
    
    def kill(self, value):
        self.fireOutput("OnKill")
        self.isNotKilled = False
        self.world.killEntity(self)

    def enable(self, value):
        """
        Enable this entity.
        """
        self.enabled = True

    def disable(self, value):
        """
        Disable this entity.
        This will prevent it from firing outputs, but it can still simulate and trigger inputs.
        """
        self.enabled = False

    def toggle(self, value):
        """
        Toggle this entity between enabled and disabled states.
        """
        self.enabled = not self.enabled
    
    def setupEventHandlers(self):
        """
        Override this method when setting up event handlers for the messenger.
        """
        pass

    def setupIO(self):
        """
        Override this method when setting up IO triggers.
        """
        pass
    
    def bindOutput(self, outputName, inputObj, inputName):
        """
        Bind outputName on this object to inputName on inputObj.
        """
        assert outputName in self.outputSpec
        self._outputBindings.setdefault(outputName, [])
        self._outputBindings[outputName].append((inputObj, inputName))
    
    def fireOutput(self, outputName, value=None):
        """
        Fire the given output outputName with the specified value.
        """
        if self.isNotKilled and self.enabled:
            for inputObj, inputName in self._outputBindings.get(outputName, []):
                inputObj.triggerInput(inputName, value)

    def _fireOutput_event(self, outputName, value=None, *_, **__):
        """
        An event-friendly version of fireOutput.
        """
        self.fireOutput(value, outputName)
    
    def triggerInput(self, inputName, value):
        """
        Trigger the given input.
        """
        if self.isNotKilled:
            assert inputName in self.inputSpec

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
        super(VisibleEntity, self).__init__(world, name, tags)
        
        self.createOGRE(model)
        self.sceneNode.setPosition(position)
        print self.sceneNode.getParent().getParent().getName()
        
    def setupEventHandlers(self):
        self.app.messenger.accept("start use: [*] '%s'" % (self.name,), self._fireOutput_event, extraArgs=['OnUse', True])
        self.app.messenger.accept("end use: [*] '%s'" % (self.name,), self._fireOutput_event, extraArgs=['OnUse', False])
    
    def createOGRE(self, value):
        if isinstance(value, basestring):
            loaded = False
            for suffix in ("", ".mesh"):
                try:
                    self.entity = self.app.sceneManager.createEntity(self.name, value + suffix)
                    loaded = True
                except ogre.OgreException, e:
                    continue
            if not loaded:
                raise e
        else:
            self._model = value

        self.sceneNode = self.world.worldNode.createChildSceneNode(self.name + "/Node")
        self.sceneNode.attachObject(self.entity)
    
    outputSpec = {
        "OnUse": (None, "Fired when a user fires this object."),
    }

    
class PhysicsEntityMotionState(bullet.btMotionState):
    def __init__(self, entity, initialTransform):
        bullet.btMotionState.__init__(self)
        self.entity    = entity
        self.transform = initialTransform
    
    def getWorldTransform(self, worldTrans):
        worldTrans.setOrigin  (self.transform.getOrigin())
        worldTrans.setRotation(self.transform.getRotation())
        
    def setWorldTransform(self, worldTrans):
        origin, rotation = worldTrans.getOrigin(), worldTrans.getRotation()
        self.transform.setOrigin(origin)
        self.transform.setRotation(rotation)
        self.entity.sceneNode.setPosition(origin.x(), origin.y(), origin.z())
        self.entity.sceneNode.setOrientation(ogre.Quaternion(rotation.w(), rotation.x(), rotation.y(), rotation.z()))

class PhysicsEntity(VisibleEntity):
    
    _physMass = None
    _physBody = None
    
    MotionState = PhysicsEntityMotionState
    physFlags   = 0

    hasGhostObject = False
    
    def __init__(self, world, name, position, model, tags="", mass=0, collisionModel=None, collisionTags=None, physShape=None):
        super(PhysicsEntity, self).__init__(world, name, position, model, "physics " + tags)
        
        self.collisionTags  = collisionTags
        self.createCollisionModel(collisionModel)
        self.createShape(physShape)
        self.createBody(mass, position)

    def createBody(self, mass, position):
        
        position = bullet.btVector3(*position)
        transform = bullet.btTransform(bullet.btQuaternion(0, 0, 0, 1), position)
        
        if self.hasGhostObject:
            body = bullet.btPairCachingGhostObject()
            body.setCollisionShape(self.physShape)
            body.setWorldTransform(transform)
            self.world.physWorld.addCollisionObject(body, getTagBits(self.tags), getTagBits(self.collisionTags))
        else:
            self.motionState = self.MotionState(self, transform)
            self.physMass = mass

            localInertia = bullet.btVector3(0, 0, 0)
            self.physShape.calculateLocalInertia(mass, localInertia)
        
            construct = bullet.btRigidBody.btRigidBodyConstructionInfo(mass, self.motionState, self.physShape, localInertia)
            body = bullet.btRigidBody(construct)
            
            self.world.physWorld.addRigidBody(body, getTagBits(self.tags), getTagBits(self.collisionTags))
        
        body.setCollisionFlags(body.getCollisionFlags() | self.physFlags)
        body.setUserData(self)
        self.physBody = body
    
    def createCollisionModel(self, value):
        if value is None:
            self.collisionEntity = self.entity
        else:
            if isinstance(value, basestring):
                self.collisionEntity = self.app.sceneManager.createEntity(self.name+"/Collision", value)
            else:
                self.collisionEntity = value
            self.sceneNode.attachObject(self.collisionEntity)
            
    def createShape(self, value):
        if value is None:
            converter = OgreBulletC.StaticMeshToShapeConverter(self.collisionEntity)
            self.physShape = converter.createTrimesh().getBulletShape()
        else:
            self.physShape = value

# Define outside because it references itself.
PhysicsEntity.outputSpec = {
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
