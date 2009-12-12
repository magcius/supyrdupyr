
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
