# from zope.interface import Interface, implements, Attribute
from panda3d.core import NodePath, BitMask32, Quat
from panda3d.ode import OdeBody, OdeTriMeshData, OdeTriMeshGeom, OdeMass
from exploratorium.util import geomId

import os.path
import itertools

geomToEnt = {}
tagRegistry = {}

def getTagBits(tags):
    bits = 0
    notBits = False
    if not tags:
        return BitMask32.allOn()
    
    if all(tag[0] == "!" for tag in tags):
        tags = [tag[1:] for tag in tags]
        notBits = True
        
    for tag in tags:
        if tag not in ("all", "*"):
            tagRegistry.setdefault(tag, len(tagRegistry))
            index = tagRegistry[tag]
            bits |= 1 << index
    
    if notBits:
        bits = ~bits
    
    return BitMask32(bits)

class StaticEntity(object):
    
    # implements(IEntity)
    
    def __init__(self, cell, name, model, tags=None):
        self._inputs       = {}
        self._inputValues  = {}
        self._outputs      = {}
        self._outputValues = {}
        
        self._cell  = cell
        self._world = cell._world
        self._data  = None
        self._name  = name
        
        self.model  = model
        self.tags   = "all * " + tags

        self._cell.addEntity(self)

    def sendEntityEvent(self, eventtype, *entities, **kwargs):
        withTags = kwargs.get('withTags', True)
        permute  = kwargs.get('permute', False)
        loop = itertools.permutations(entities) if permute else [entities]
        for ents in loop:
            ents = ((["'%s'" % ent.name] + (["[%s]" % tag for tag in ent.tags] if withTags else [])) for ent in ([self] + list(ents)))
            for enttags in itertools.product(*ents):
                messenger.send("%s: %s" % (eventtype, ' '.join(enttags)), [self] + list(ents))
    
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
            self._model = loader.loadModel(os.path.join(MODELS_DIR, value))
            self._model.setPos(0, 0, 0)
            self._model.setScale(1, 1, 1)
        else:
            self._model = value
            
        if self._cell == self:
            self._model.reparentTo(render)
        else:
            self._model.reparentTo(self._cell.model)

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
        self._model.setPos(x, y, z)

    def setRotation(self, h, p, r):
        self._model.setRot(h, p, r)

    def setQuaternion(self, quat):
        self._model.setQuat(quat)

    @property
    def world(self):
        return self._world

    @property
    def cell(self):
        return self._cell

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
            self._outputs[outputName] = (obj.triggerInput, [inputName], None)
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
        
class CollidableEntity(StaticEntity):

    # implements(ICollidableEntity)
    
    def __init__(self, cell, name, model, tags=None, collisionModel=None, collisionTags=None, physGeom=None):
        StaticEntity.__init__(self, cell, name, model, tags)
        self.collisionTags  = collisionTags
        self.collisionModel = collisionModel
        self.physGeom       = physGeom

    @property
    def collisionModel(self):
        return self._colModel

    @collisionModel.setter
    def collisionModel(self, value):
        if value is None:
            self._colModel = self._model
        else:
            if isinstance(value, basestring):
                self._colModel = NodePath(value)
                self._colModel.setPos(0, 0, 0)
                self._colModel.setScale(1, 1, 1)
            else:
                self.colModel = value
            self._colModel.reparentTo(self._model)
        self._colModel.flattenLight()

    @property
    def physGeom(self):
        return self._physGeom

    @physGeom.setter
    def physGeom(self, value):
        if value is None:
            trimesh = OdeTriMeshData(self._colModel, True)
            self._physGeom = OdeTriMeshGeom(self._world.physSpace, trimesh)
        else:
            self._physGeom = value
            
        self._physGeom.setCollideBits(getTagBits(self.collisionTags))
        self._physGeom.setCategoryBits(getTagBits(self.tags))
        geomToEnt[geomId(self._physGeom)] = self

    def setPosition(self, x, y, z):
        self._model.setPos(x, y, z)
        print "Setting GEOM position: %d %d %d" % (self._model.getX(render), self._model.getY(render), self._model.getZ(render))
        self._physGeom.setPosition(self._model.getX(render), self._model.getY(render), self._model.getZ(render))

    def setRotation(self, h, p, r):
        self._model.setRot(h, p, r)
        self._physGeom.setRotation(h, p, r)

    def setQuaternion(self, quat):
        self._model._setQuat(quat)
        self._physGeom.setQuaternion(quat)

class PhysicsEntity(CollidableEntity):
    
    _physMass = None
    _physBody = None
    
    def __init__(self, cell, name, model, mass, tags=None, collisionModel=None, physGeom=None):
        CollidableEntity.__init__(self, cell, name, model, tags, collisionModel, physGeom)
        self.physBody = OdeBody(self._world.physWorld)
        self.physMass = mass

    @property
    def physGeom(self):
        return CollidableEntity.physGeom.fget(self)
    
    @physGeom.setter
    def physGeom(self, value):
        CollidableEntity.physGeom.fset(self, value)
        if self._physBody is not None:
            self._physGeom.setBody(self._physBody)
    
    @property
    def physBody(self):
        return self._physBody

    @physBody.setter
    def physBody(self, value):
        self._physBody = value
        self._physBody.setPosition(self._model.getPos(render))
        self._physBody.setQuaternion(self._model.getQuat(render))
        if self._physMass is not None:
            self._physBody.setMass(self._physMass)
        self._physGeom.setBody(self._physBody)

    @property
    def physMass(self):
        return self._physMass

    @physMass.setter
    def physMass(self, value):
        if isinstance(value, (int, float)):
            b1, b2 = self._model.getTightBounds()
            wx, wy, wz = b1 - b2
            self._physMass = OdeMass()
            self._physMass.setBox(value, abs(wx), abs(wy), abs(wz))
        elif isinstance(value, (OdeMass)):
            self._physMass = value
        self._physBody.setMass(self._physMass)

    def setPosition(self, x, y, z):
        self._model.setPos(x, y, z)
        print "Setting PHYS position: %d %d %d" % (self._model.getX(render), self._model.getY(render), self._model.getZ(render))
        self._physBody.setPosition(self._model.getX(render), self._model.getY(render), self._model.getZ(render))

    def setRotation(self, h, p, r):
        self._model.setRot(h, p, r)
        self._physBody.setRotation(h, p, r)

    def setQuaternion(self, quat):
        self._model._setQuat(quat)
        self._physBody.setQuaternion(quat)

    def simulate(self):
        pos = self._physBody.getPosition()
        quat = Quat(self._physBody.getQuaternion())
        self._model.setPosQuat(render, pos, quat)
