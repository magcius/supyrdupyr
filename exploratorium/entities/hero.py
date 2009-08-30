class Hero(PhysicsEntity):
    
    def __init__(self, cell, model, name, mass, kind=None, collisionModel=None, geom=None):
        PhysicsEntity.__init__(self, cell, model, name, mass, kind, collisionModel, geom)
    
    def getLocation(self):
        return cell
        #FIXME
        #Need to check what cell I'm currently above
