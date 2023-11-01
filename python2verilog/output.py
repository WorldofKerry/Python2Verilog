def func101(n0):
    a0 = 0
    b0 = 1
    i0 = 0
    yield from func106(a0, b0, i0, n0)


def func106(a1, b1, i1, n0):
    if i1 < n0:
        if a1 % 2:
            a2 = a1 + 10
            yield {a2}
            yield from func114(a2, i1, b1, n0)
        else:
            yield from func114(a1, i1, b1, n0)
    else:
        return


def func114(a3, i1, b1, n0):
    a4 = b1
    b2 = a3 + b1
    i3 = i1 + 1
    yield from func106(a4, b2, i3, n0)


inst = func101(50)
for _ in range(20):
    print(next(inst))
