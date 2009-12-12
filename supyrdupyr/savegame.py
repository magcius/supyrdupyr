
try:
    import cPickle as pickle
except ImportError:
    import pickle


class SaveGame(object):
    pass

def load(filename):
    sg = pickle.load(open(filename))
    assert isinstance(sg, SaveGame)
    return sg

def new():
    return SaveGame()

def save(sg, filename):
    pickle.dump(open(filename))
