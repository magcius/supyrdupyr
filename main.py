#            
#            Exploration Concept Demo
#            (c) magcius and mike 2009
#            
#            Notes here.
#            



import direct.directbase.DirectStart
from pandac.PandaModules import *
 
from direct.task import Task
from direct.actor import Actor
from direct.interval.IntervalGlobal import *
import math, sys

# Debug
#    0 - no debug info
#    1 - some data
#    2 - all data
#  When adding new things, general things should be 
#        if DEBUG == 1, specific or spammy should be
#        if DEBUG == 2

DEBUG = 2

# App class contains World class, no init parameters.
# *   handles input and passes it to World.
# *   handles graphics rendering.
# *   will handle sound output.
# *   currently has a Player hardcoded in.

# World class contains Player class along with entities
#            init: parent(App), Player(bool)
# *   handles game logic and object positions and movement
# *   takes player input information from App
# *   equates to one cell
# *   creating one with Player set to true will init a player
#                             and set the parent player to it

# Player class contains entity for graphics, logic for self
#            init: parent(World)
# *   handles position for self, logic for self
# *   can only belong to one World at one point.
# *   begins in the World that spawns it
  
class App(object):
    
    World = 0
    Player = 0
    
    def __init__(self):
        if DEBUG >= 1:
            print "Initialising application."
        self.World = World(self,True)
        if self.Player == 0:
            print "Error 404: Player does not exist."
            sys.exit(0)
        
        
        #temporary model until Worlds are finished
        self.env = loader.loadModel("models/field2.egg")
        self.env.reparentTo(render)
        self.env.setScale(1.00,1.00,1.00)
        self.env.setPos(0,0,0)
        

        base.disableMouse()
        base.camera.setPos(self.Player.x,self.Player.y-10,self.Player.z + 2)
        ##not set to point at the player yet, direction static
        
        if DEBUG >= 1:
            print "Initialised application."
    
    def simulate(self,task):
        ##debug movement to test.
        self.Player.x -= 0.05
        self.Player.y += 0.009
        self.Player.simulate()
        
        base.camera.setPos(self.Player.x,self.Player.y-10,self.Player.z + 2)
        
        return Task.cont


class World(object):
    
    Player = 0
    Parent = 0
    
    def __init__(self,parent,pl):
        if DEBUG == 2:
            print ".Initialising world."
        self.Parent = parent
        if pl == True:
            self.Player = Player(self)
            if DEBUG == 2:
                print "..Player created."
            self.Parent.Player = self.Player
            if DEBUG == 2:
                print ".Replaced App player with created one."
        if DEBUG >= 1:
            print ".World initialised."

class Player(object):
    
    Parent = 0
    Actor = 0
    x = 0
    y = 0
    z = 0
    direction = 0
    
    def __init__(self,parent):
        if DEBUG == 2:
            print "..Player initialising."
        self.Parent = parent
        self.x = 0
        self.y = 0
        self.z = 3
        self.direction = 0
        self.Actor = Actor.Actor("models/jeff.egg")
        self.Actor.setScale(1.0,1.0,1.0)
        self.Actor.setPos(self.x,self.y,self.z)
        self.Actor.reparentTo(render)
        if DEBUG >= 1:
            print "..Player initalised."
    
    def simulate(self):
        self.Actor.setPos(self.x,self.y,self.z)



if __name__ == '__main__':
    app = App()
    
    #stuff here
    taskMgr.add(app.simulate, "SimulateTask")
    
    run()
    
    
