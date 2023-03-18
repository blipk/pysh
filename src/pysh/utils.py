def repr_(cls) -> str:
    classname = cls.__class__.__name__
    args = ", ".join(
        [f"{k}={repr(v)}" for (k, v) in cls.__dict__.items()])
    return f"{classname}({args})"
