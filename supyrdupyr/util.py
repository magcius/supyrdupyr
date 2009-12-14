
def diagonal(L, offset=0):
    L = list(L)
    for i in xrange(offset, offset+len(L)):
        if 0 <= i < len(L):
            SL = L[i]
            if i < len(SL):
                yield SL[i]


def clamp(num, min_, max_):
    return min(max_, max(min_, num))

def methodSignature(f, args, kwargs):
    argstring = ', '.join(str(a) for a in args)
    if kwargs:
        argstring += ', ' + ', '.join("%s=%s" % t for t in kwargs.iteritems())
    return "%s(%s)" % (f.__name__, argstring)

def multiplyVec3(vec, scalar):
    from ogre.physics import bullet as bt
    return bt.btVector3(vec.x() * scalar, vec.y() * scalar, vec.z() * scalar)

def multiplyQuat(quat, scalar):
    from ogre.physics import bullet as bt
    return bt.btQuaternion(quat.x() * scalar, quat.y() * scalar, quat.z() * scalar, quat.w() * scalar)

def vecStr(vec):
    return '[%f, %f, %f, %f]' % (vec.x(), vec.y(), vec.z(), vec.w())

def matStr(mat):
    return '[%s,\n %s,\n %s]' % (vecStr(mat[0]), vecStr(mat[1]), vecStr(mat[2]))
