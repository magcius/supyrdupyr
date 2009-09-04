from pandac.PandaModules import OdeMass, OdeSphereGeom, Mat3
from exploratorium.entities import PhysicsEntity

SPEED = 10
JUMP_FORCE = 10

class Hero(PhysicsEntity):
    
    def __init__(self, cell):
        
        mass = OdeMass()
        mass.setSphere(density=10, radius=0.125)
        
        PhysicsEntity.__init__(self, cell, "models/jeff", "hero", mass, "physics hero")

        self.physGeom = OdeSphereGeom(self._world.physSpace, 0.125)

        base.accept("collided: [hero] [*]",    self._collidedWithAnything)
        base.accept("collided: [hero] [cell]", self._collidedWithCell)

        base.accept("w", self.addTask, [self.move, 0, SPEED])
        base.accept("w-up", self.removeTask, [self.move, 0, SPEED])
        
        base.accept("s", self.addTask, [self.move, 0, -SPEED])
        base.accept("s-up", self.removeTask, [self.move, 0, -SPEED])
        
        base.accept("a", self.addTask, [self.move, -SPEED, 0])
        base.accept("a-up", self.removeTask, [self.move, -SPEED, 0])
        
        base.accept("d", self.addTask, [self.move, SPEED, 0])
        base.accept("d-up", self.removeTask, [self.move, SPEED, 0])
        
        self.canJump = False
        self.tasks = []
    
    def _collidedWithAnything(self, _, other):
        self.canJump = True

    def _collidedWithCell(self, _, cell):
        self.cell = cell
    
    def move(self, x, y):
        self.physBody.addRelForce(x, y, 0)

    def jump(self):
        if self.canJump:
            self.physBody.addForce(0, 0, 10)
            self.canJump = False

    def simulate(self):
        self.physBody.setAngularVel(0, 0, 0)
        self.physBody.setRotation(Mat3.identMat())

        for func, args in self.tasks:
            func(*args)
        
        PhysicsEntity.simulate(self)

    def addTask(self, func, *args):
        self.tasks.append((func, args))

    def removeTask(self, func, *args):
        self.tasks.remove((func, args))
        
    @property
    def location(self):
        return self.cell
