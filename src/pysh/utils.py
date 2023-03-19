def repr_(cls, incl=True) -> str:
    classname = cls.__class__.__name__
    dct = cls.__dict__ if hasattr(cls, "__dict__") else cls
    args = ", ".join(
        [f"{k}={repr(v)}" for (k, v) in dct.items()
        if incl is True or (k in incl)])
    return f"{classname}({args})"

from functools import wraps
from time import time

def timeit(f):
    @wraps(f)
    def wrap(*args, **kw):
        ts = time()
        result = f(*args, **kw)
        te = time()
        print("func:%r took: %2.4f sec \n args:[%r, %r]" % \
          (f.__name__, args[0:1], kw, te-ts))
        return result
    return wrap