

import direct.directbase.DirectStart

from direct.task import Task

import os.path
import __builtin__

__builtin__.BASE_DIR   = os.path.abspath(os.path.dirname(__file__))
__builtin__.MODELS_DIR = os.path.join(BASE_DIR, "models")

from exploratorium import world as M_world
from exploratorium.entities import hero as M_hero

def tick(self):
    world.updateWorld()
    return Task.cont

world = M_world.world
hero = M_hero.Hero(world.root)
rootModel = world.root.model
world.root.show()
hero.setPosition(0, 0, 10)

base.setFrameRateMeter(True)

# base.buttonThrowers[0].node().setModifierButtons(ModifierButtons())

render.prepareScene(base.win.getGsg())

taskMgr.doMethodLater(0.5, tick, "enter frame task")

run()
