def func101(n0):
    a0 = 0
    b0 = 1
    i0 = 0
    a1 = a0
    b1 = b0
    i1 = i0
    a1 = a0
    b1 = b0
    i1 = i0
    if i1 < n0:
        if a1 % 2:
            a2 = a1
            yield {a2}
            yield from func138(b1, n0, a2, i1)
        else:
            a3 = a1
            a3 = a1
            a4 = b1
            b2 = a3 + b1
            i3 = i1 + 1
            a1 = a4
            b1 = b2
            i1 = i3
            a1 = a4
            b1 = b2
            i1 = i3
            if i1 < n0:
                if a1 % 2:
                    a2 = a1
                    yield {a2}
                    yield from func138(b1, n0, a2, i1)
                else:
                    yield from func123(a1, i1, b1, n0)
            else:
                return
    else:
        return


def func138(b1, n0, a2, i1):
    a3 = a2
    a3 = a2
    a4 = b1
    b2 = a3 + b1
    i3 = i1 + 1
    yield from func128(a4, b2, i3, n0)


def func128(a1, b1, i1, n0):
    if i1 < n0:
        if a1 % 2:
            a2 = a1
            yield {a2}
            yield from func138(b1, n0, a2, i1)
        else:
            yield from func123(a1, i1, b1, n0)
    else:
        return


def func123(a3, i1, b1, n0):
    a4 = b1
    b2 = a3 + b1
    i3 = i1 + 1
    yield from func128(a4, b2, i3, n0)


inst = func101(50)
for _ in range(20):
    print(next(inst))
