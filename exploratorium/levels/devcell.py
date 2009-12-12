
from supyrdupyr.entities import StaticEntity
from supyrdupyr.world import Cell

class DevCell(Cell):
    def __init__(self, world, name):
        Cell.__init__(self, world, name, "devcell.mesh", "dev")
