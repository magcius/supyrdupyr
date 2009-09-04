

def diagonal(L, offset=0):
    L = list(L)
    for i in xrange(offset, offset+len(L)):
        if 0 <= i < len(L):
            SL = L[i]
            if i < len(SL):
                yield SL[i]
