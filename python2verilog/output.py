def func138(a1, b1, i1, n0):
    if i1 < n0:
        if a1 % 2:
            a4 = a1
            yield {a4}
            yield from func116(a4, i1, n0, b1)
        else:
            a2 = a1
            a2 = a1
            a3 = b1
            b2 = a2 + b1
            i3 = i1 + 1
            a1 = a3
            b1 = b2
            i1 = i3
            a1 = a3
            b1 = b2
            i1 = i3
            if i1 < n0:
                if a1 % 2:
                    a4 = a1
                    yield {a4}
                    yield from func116(a4, i1, n0, b1)
                else:
                    yield from func116(a1, i1, n0, b1)
            else:
                return
    else:
        return


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
            a4 = a1
            yield {a4}
            yield from func116(a4, i1, n0, b1)
        else:
            yield from func116(a1, i1, n0, b1)
    else:
        return


def func116(a2, i1, n0, b1):
    a3 = b1
    b2 = a2 + b1
    i3 = i1 + 1
    a1 = a3
    b1 = b2
    i1 = i3
    a1 = a3
    b1 = b2
    i1 = i3
    if i1 < n0:
        if a1 % 2:
            a4 = a1
            yield {a4}
            yield from func116(a4, i1, n0, b1)
        else:
            a2 = a1
            a2 = a1
            a3 = b1
            b2 = a2 + b1
            i3 = i1 + 1
            yield from func138(a3, b2, i3, n0)
    else:
        return


inst = func101(50)
for _ in range(20):
    print(next(inst))
