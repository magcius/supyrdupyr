from direct.directbase import DirectStart
from pandac.PandaModules import OdeWorld, OdeSimpleSpace, OdeJointGroup, OdePlaneGeom
from pandac.PandaModules import OdeBody, OdeMass, OdeBoxGeom, OdeTriMeshData, OdeTriMeshGeom
from pandac.PandaModules import BitMask32, CardMaker, Vec4, Quat
from random import randint, random
from direct.task import Task
 
# Setup our physics world
world = OdeWorld()
world.setGravity(0, 0, -9.81)

# The surface table is needed for autoCollide
world.initSurfaceTable(1)
world.setSurfaceEntry(0, 0, 150, 0.0, 9.1, 0.9, 0.00001, 0.0, 0.002)
 
# Create a space and add a contactgroup to it to add the contact joints
space = OdeSimpleSpace()
space.setCollisionEvent("collided")
space.setAutoCollideWorld(world)
contactgroup = OdeJointGroup()
space.setAutoCollideJointGroup(contactgroup)
 
# Load the box
box = loader.loadModel("box")
# Make sure its center is at 0, 0, 0 like OdeBoxGeom
box.setPos(-.5, -.5, -.5)
box.flattenLight() # Apply transform
box.setTextureOff()
 
# Add a random amount of boxes
boxes = []
#for i in range(randint(15, 30)):
# Setup the geometry
boxNP = box.copyTo(render)
boxNP.setPos(0, 0, 8)
boxNP.setColor(random(), random(), random(), 1)
# Create the body and set the mass
boxBody = OdeBody(world)
M = OdeMass()
M.setBox(50, 1, 1, 1)
boxBody.setMass(M)
boxBody.setPosition(boxNP.getPos(render))
boxBody.setQuaternion(boxNP.getQuat(render))
# Create a BoxGeom
boxGeom = OdeBoxGeom(space, 1, 1, 1)
boxGeom.setCollideBits(BitMask32.allOn())
boxGeom.setCategoryBits(BitMask32.allOn())
boxGeom.setBody(boxBody)
boxes.append((boxNP, boxBody))
 
# Add a plane to collide with
ground = loader.loadModel("models/plane.egg")
ground.flattenLight()
ground.reparentTo(render)
ground.setPos(0, 0, 5)

envCollideTrimesh = OdeTriMeshData(ground, True)
envCollideGeom = OdeTriMeshGeom(space, envCollideTrimesh)
envCollideGeom.setPosition(0, 0, 5)
envCollideGeom.setCategoryBits(BitMask32.allOn())
envCollideGeom.setCollideBits(BitMask32.allOn())

# groundGeom = OdePlaneGeom(space, Vec4(0, 0, 2, 0))
# groundGeom.setCollideBits(BitMask32.allOn())
# groundGeom.setCategoryBits(BitMask32.allOn())

# Set the camera position
base.disableMouse()
base.camera.setPos(40, 40, 20)
base.camera.lookAt(0, 0, 0)

# The task for our simulation
def simulationTask(task):
  space.autoCollide() # Setup the contact joints
  # Step the simulation and set the new positions
  world.quickStep(globalClock.getDt())
  ground.setPosQuat(render, envCollideGeom.getPosition(), envCollideGeom.getQuaternion())
  for np, body in boxes:
    np.setPosQuat(render, body.getPosition(), Quat(body.getQuaternion()))
  contactgroup.empty() # Clear the contact joints
  return task.cont
  
def collided(entry):
  return Task.cont

base.accept("collided", collided)
  
# Wait a split second, then start the simulation  
taskMgr.doMethodLater(0.5, simulationTask, "Physics Simulation")
 
run()
