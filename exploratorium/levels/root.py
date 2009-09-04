
from pandac.PandaModules import OdePlaneGeom, Vec4

from exploratorium.entities import StaticEntity
from exploratorium.world import Cell

class DevCell(Cell):
    def __init__(self, world, name):
        Cell.__init__(self, world, name, "devcell.egg", "dev")
