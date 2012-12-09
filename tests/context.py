import os
import sys
sys.path.insert(0, os.path.abspath('..'))

from nose.tools import make_decorator

import taxon


def benchmark():
    def decorate(func):
        def newfunc(*arg, **kw):
            import time
            start = time.time()
            ret = func(*arg, **kw)
            end = time.time()
            sys.stderr.write('%s took %2fs\n' % (func.__name__, end - start))
            return ret
        newfunc = make_decorator(func)(newfunc)
        return newfunc
    return decorate
