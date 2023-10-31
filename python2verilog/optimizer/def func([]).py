def func(i1, c1):
    if i1 < a0:
        c2 = c1 + b0
        i2 = i1 + 1
        if (i1 + 1) < a0:
            c2 = (c1 + b0) + b0
            i2 = (i1 + 1) + 1
            if ((i1 + 1) + 1) < a0:
                c2 = ((c1 + b0) + b0) + b0
                i2 = ((i1 + 1) + 1) + 1
            else:
                return [(c1 + b0) + b0]
        else:
            return [c1 + b0]
    else:
        return [c1]
