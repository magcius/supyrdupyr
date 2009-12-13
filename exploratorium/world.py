
from supyrdupyr.world import World as sdWorld
from exploratorium.levels.devcell import DevCell as d, RootDevCell as r

class World(sdWorld):
    cellMap = \
[[r, d, d, d,],
 [d, d, d, d,],
 [d, d, d, d,],
 [d, d, d, d,],]
