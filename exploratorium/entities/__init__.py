# from zope.interface import Interface, implements, Attribute
from pandac.PandaModules import NodePath, OdeBody, OdeTriMeshData, OdeTriMeshGeom, OdeMass, BitMask32
from direct.showbase.DirectObject import DirectObject

# class IEntity(Interface):
#     name  = Attribute("The unique name associated with this entity.")
#     kind  = Attribute("The kind of entity this is. Kinds are application-specific.")
#     model = Attribute("The model (NodePath) associated with this entity.")
#     data  = Attribute("Extra data associated with this entity.")
#     cell  = Attribute("The cell this entity is in.")
#     world = Attribute("The world this entity is in.")

#     def setPosition(x, y, z):
#         pass

#     def setRotation(h, p, r):
#         pass

#     def setQuaternion(quat):
#         pass

#     def bindOutput(outputName, inputObj, inputName, func, args, filter):
#         pass

#     def bindInput(inputName, outputObj, outputName, func, args, filter):
#         pass

#     def bindInputHandler(inputName, func):
#         pass
    
#     def triggerOutput(value, outputName):
#         pass

#     def triggerInput(value, inputName):
#         pass

#     def simulate():
#         pass

# class ICollidableEntity(IEntity):
#     collisionModel = Attribute("The collision model (NodePath) associated with this "
#                                "entity, or, None to have the collision model be the "
#                                "same as the visible model.")
#     physGeom       = Attribute("The ODE physics geometry. Leave None to have a "
#                                "TriMesh generated at constructor time.")
    
# class IPhysicsEntity(ICollidableEntity):
#     physBody = Attribute("The ODE physics body object.")
#     physMass = Attribute("The ODE physics mass object.")

# # class IInteractiveEntity(IEntity):
# #     triggers = Attribute("Return an iterable of ITrigger objects that define "
# #                          "the triggers of this object, such as key presses, "
# #                          "mouse clicks, entering and exiting the bounds. "
# #                          "See triggers.py for a list of possible triggers.")
        
# #     def addTrigger(trigger):
# #         ''' Add a trigger to the trigger list. '''

# #     def removeTrigger(trigger):
# #         ''' Remove a trigger from the trigger list. '''

geomToEnt = {}

class StaticEntity(object, DirectObject):
    
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
            self._model = NodePath(value)
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
    
    def __init__(self, cell, name, model, tags=None, collisionModel=None, physGeom=None):
        StaticEntity.__init__(self, cell, name, model, tags)
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
            self._world.physSpace.add(self._physGeom)
            
        self._physGeom.setCollideBits (BitMask32.allOn())
        self._physGeom.setCategoryBits(BitMask32.allOn())
        
        geomToEnt[self._physGeom] = self
    
    def setPosition(self, x, y, z):
        self._model.setPos(x, y, z)
        self._physGeom.setPosition(x, y, z)

    def setRotation(self, h, p, r):
        self._model.setRot(h, p, r)
        self._physGeom.setRotation(h, p, r)

    def setQuaternion(self, quat):
        self._model._setQuat(quat)
        self._physGeom.setQuaternion(quat)

class PhysicsEntity(CollidableEntity):

    # implements(IPhysicsEntity)
    _physMass = None
    
    def __init__(self, cell, name, model, mass, tags=None, collisionModel=None, physGeom=None):
        CollidableEntity.__init__(self, cell, name, model, tags, collisionModel, physGeom)
        self.physBody = OdeBody(self._world.physWorld)
        self.physMass = mass

    @property
    def physBody(self):
        return self._physBody

    @physBody.setter
    def physBody(self, value):
        self._physBody = value
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
        self._physBody.setPosition(x, y, z)

    def setRotation(self, h, p, r):
        self._model.setRot(h, p, r)
        self._physBody.setRotation(h, p, r)

    def setQuaternion(self, quat):
        self._model._setQuat(quat)
        self._physBody.setQuaternion(quat)

    def simulate(self):
        self._model.setPosQuat(render, self._physBody.getPosition(), Quat(self._physBody.getQuaternion()))
