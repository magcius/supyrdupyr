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
  
class App:
    
    World = 0
    Player = 0
    
    def __init__(self):
        if DEBUG >= 1:
            print "Initialising application."
        self.World = World(self,True)
        if self.Player == 0:
            print "Error 404: Player does not exist."
            sys.exit(0)
        
        env = loader.loadModel("models/field2.egg")
        env.reparentTo(render)
        env.setScale(1.00,1.00,1.00)
        env.setPos(0,0,0)
        
        
        
        if DEBUG >= 1:
            print "Initialised application."


class World:
    
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

class Player:
    
    Parent = 0
    
    def __init__(self,parent):
        if DEBUG == 2:
            print "..Player initialising."
        self.Parent = parent
        if DEBUG >= 1:
            print "..Player initalised."



if __name__ == '__main__':
    app = App()
    
    #stuff here
    
    run()
    
    
