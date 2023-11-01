def func101(b0, a0):
    if 0 < a0:
        if 1 < a0:
            if 2 < a0:
                yield from func123(3, ((0 + b0) + b0) + b0, b0, a0)
            else:
                yield [(0 + b0) + b0]
        else:
            yield [0 + b0]
    else:
        yield [0]


def func123(i1, c1, b0, a0):
    if i1 < a0:
        if (i1 + 1) < a0:
            if ((i1 + 1) + 1) < a0:
                yield from func123(((i1 + 1) + 1) + 1, ((c1 + b0) + b0) + b0, b0, a0)
            else:
                yield [(c1 + b0) + b0]
        else:
            yield [c1 + b0]
    else:
        yield [c1]


inst = func101(50, 10)
for _ in range(20):
    print(next(inst))
