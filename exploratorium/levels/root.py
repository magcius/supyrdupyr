
from exploratorium.world import Cell

class DevCell(Cell):
    def __init__(self, world, name):
        Cell.__init__(self, world, name, "models/devcell", "dev")

        self.bindInputHandler("left cell", self.leaveCell)
        self.bindInputHandler("enter cell", self.enterCell)

    def leaveCell(self, value):
        pass

    def enterCell(self, value):
        pass
