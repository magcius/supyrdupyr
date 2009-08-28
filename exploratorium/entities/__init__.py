from zope.interface import Interface, implements, Attribute
from pandac.PandaModules import OdeBody

class IEntity(Interface):
    name  = Attribute("The unique name associated with this entity.")
    kind  = Attribute("The kind of entity this is. Kinds are application-specific.")
    model = Attribute("The model (NodePath) associated with this entity.")
    data  = Attribute("Extra data associated with this entity.")
    cell  = Attribute("The cell this entity is in.")
    world = Attribute("The world this entity is in.")

    def setPosition(x, y, z):
        pass

    def setRotation(h, p, r):
        pass

    def setQuaternion(quat):
        pass

    def bindOutput(outputName, inputObj, inputName, func, args, filter):
        pass

    def bindInput(inputName, outputObj, outputName, func, args, filter):
        pass

    def bindInputHandler(inputName, func):
        pass
    
    def triggerOutput(value, outputName):
        pass

    def triggerInput(value, inputName):
        pass

class ICollidableEntity(IEntity):
    collisionModel = Attribute("The collision model (NodePath) associated with this "
                               "entity, or, None to have the collision model be the "
                               "same as the visible model.")
    physGeom       = Attribute("The ODE physics geometry. Leave None to have a "
                               "TriMesh generated at constructor time.")
    
class IPhysicsEntity(ICollidableEntity):
    physBody = Attribute("The ODE physics body object.")

# class IInteractiveEntity(IEntity):
#     triggers = Attribute("Return an iterable of ITrigger objects that define "
#                          "the triggers of this object, such as key presses, "
#                          "mouse clicks, entering and exiting the bounds. "
#                          "See triggers.py for a list of possible triggers.")
        
#     def addTrigger(trigger):
#         ''' Add a trigger to the trigger list. '''

#     def removeTrigger(trigger):
#         ''' Remove a trigger from the trigger list. '''

class StaticEntity(object):
    
    implements(IStaticEntity)
    
    def __init__(self, cell, name, model, kind=None):
        self._inputs      = {}
        self._inputValues = {}
        self._outputs     = {}
        
        self._cell  = cell
        self._world = cell.world
        self._model = model
        self._name  = name
        self._kind  = kind
        self._data  = None

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
        self._model = value

    @property
    def kind(self):
        return self._kind

    @kind.setter
    def kind(self, value):
        self._kind = value
        
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
             func, args, filter = self._outputs[outputName]
             func(filter(value), *args)

    def triggerInput(self, value, inputName):
        if inputName in self._inputs:
            self._inputValues[inputName] = value
            self._inputs[inputName](value)

    def getInput(self, inputName):
        try:
            return self._inputValues[inputName]
        except KeyError:
            return None
    
class CollidableEntity(StaticEntity):

    implements(ICollidableEntity)
    
    def __init__(self, cell, name, model, kind=None, collisionModel=None, physGeom=None):
        super(CollidableEntity, self).__init__(world, model, name, kind)
        self.collisionModel = collisionModel
        self.physGeom       = physGeom

    @property
    def collisionModel(self):
        return self._colModel

    @collisionModel.setter
    def collisionModel(self, value):
        if value is None:
            self.colModel = model
        else:
            self.colModel = value
        self._colModel.flattenLight()

    @property
    def physGeom(self):
        return self._physGeom

    @property
    def physGeom(self, value):
        if value is None:
            trimesh = OdeTriMeshData(self._colModel, True)
            self._physGeom = OdeTriMeshGeom(self._world.space, trimesh)
        else:
            self._physGeom = value

    physGeom = property(self.getPhysGeom, self.setPhysGeom)
    
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

    implements(IPhysicsEntity)
    
    def __init__(self, cell, model, name, kind=None, collisionModel=None, physGeom=None):
        super(PhysicsEntity, self).__init__(cell, model, name, kind, collisionModel, physGeom)
        self._physBody = OdeBody(self._world)

    @property
    def physBody(self):
        return self._physBody

    @physBody.setter
    def physBody(self, value):
        self._physBody = value

    def setPosition(self, x, y, z):
        self._model.setPos(x, y, z)
        self._physBody.setPosition(x, y, z)

    def setRotation(self, h, p, r):
        self._model.setRot(h, p, r)
        self._physBody.setRotation(h, p, r)

    def setQuaternion(self, quat):
        self._model._setQuat(quat)
        self._physBody.setQuaternion(quat)
