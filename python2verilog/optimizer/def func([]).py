def func(b0, a0):
    i0 = 0
    c0 = 0
    i1 = 0
    c1 = 0
    if i1 < a0:
        c2 = 0 + b0
        i2 = 1
        i1 = 1
        c1 = 0 + b0
        if i1 < a0:
            c2 = (0 + b0) + b0
            i2 = 2
            i1 = 2
            c1 = (0 + b0) + b0
            if i1 < a0:
                c2 = ((0 + b0) + b0) + b0
                i2 = 3
                i1 = 3
                c1 = ((0 + b0) + b0) + b0
            else:
                return [c1]
        else:
            return [c1]
    else:
        return [c1]
