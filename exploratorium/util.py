

def diagonal(L, offset=0):
    L = list(L)
    for i in xrange(offset, offset+len(L)):
        if 0 <= i < len(L):
            SL = L[i]
            if i < len(SL):
                yield SL[i]


def geomId(geom):
    return str(geom).split()[2][:-1]

def clamp(num, min_, max_):
    return min(max_, max(min_, num))
