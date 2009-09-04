

import direct.directbase.DirectStart
from direct.task import Task
from exploratorium import world as M_world
from exploratorium.entities import hero as M_hero    

def tick(task):
    messenger.send("enter frame")
    return Task.cont

world = M_world.world
hero = M_hero.Hero(world.root)
rootModel = world.root.model
hero.setPosition(rootModel.getX(render), rootModel.getY(render), 10)

taskMgr.add(tick, "SimulateTask")

run()
