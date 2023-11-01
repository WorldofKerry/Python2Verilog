def func163(a1, n0, b1, i1):
    a2 = b1
    b2 = a1 + b1
    i3 = i1 + 1
    i1 = i3
    b1 = b2
    a1 = a2
    if i1 < n0:
        if a1 % 2:
            yield [a1]
            yield from func163(a1, n0, b1, i1)
        else:
            a2 = b1
            b2 = a1 + b1
            i3 = i1 + 1
            i1 = i3
            b1 = b2
            a1 = a2
            if i1 < n0:
                if a1 % 2:
                    yield [a1]
                    yield from func163(a1, n0, b1, i1)
                else:
                    a2 = b1
                    b2 = a1 + b1
                    i3 = i1 + 1
                    yield from func133(a2, b2, i3, n0)
            else:
                return
    else:
        return


def func133(a1, b1, i1, n0):
    if i1 < n0:
        if a1 % 2:
            yield [a1]
            yield from func163(a1, n0, b1, i1)
        else:
            a2 = b1
            b2 = a1 + b1
            i3 = i1 + 1
            i1 = i3
            b1 = b2
            a1 = a2
            if i1 < n0:
                if a1 % 2:
                    yield [a1]
                    yield from func163(a1, n0, b1, i1)
                else:
                    a2 = b1
                    b2 = a1 + b1
                    i3 = i1 + 1
                    i1 = i3
                    b1 = b2
                    a1 = a2
                    if i1 < n0:
                        if a1 % 2:
                            yield [a1]
                            yield from func163(a1, n0, b1, i1)
                        else:
                            a2 = b1
                            b2 = a1 + b1
                            i3 = i1 + 1
                            yield from func133(a2, b2, i3, n0)
                    else:
                        return
            else:
                return
    else:
        return


def func101(n0):
    a0 = 0
    b0 = 1
    i0 = 0
    i1 = i0
    b1 = b0
    a1 = a0
    if i1 < n0:
        if a1 % 2:
            yield [a1]
            yield from func163(a1, n0, b1, i1)
        else:
            a2 = b1
            b2 = a1 + b1
            i3 = i1 + 1
            i1 = i3
            b1 = b2
            a1 = a2
            if i1 < n0:
                if a1 % 2:
                    yield [a1]
                    yield from func163(a1, n0, b1, i1)
                else:
                    a2 = b1
                    b2 = a1 + b1
                    i3 = i1 + 1
                    i1 = i3
                    b1 = b2
                    a1 = a2
                    if i1 < n0:
                        if a1 % 2:
                            yield [a1]
                            yield from func163(a1, n0, b1, i1)
                        else:
                            a2 = b1
                            b2 = a1 + b1
                            i3 = i1 + 1
                            yield from func133(a2, b2, i3, n0)
                    else:
                        return
            else:
                return
    else:
        return


inst = func101(50)
for _ in range(20):
    print(next(inst))
