def func101(n0):
    if 0 < n0:
        if 0:
            yield [0]
            yield from func163(1, 0, n0, 0)
        else:
            if 1 < n0:
                if 1:
                    yield [1]
                    yield from func163(1, 1, n0, 1)
                else:
                    if 2 < n0:
                        if 1:
                            yield [1]
                            yield from func163(2, 1, n0, 2)
                        else:
                            yield from func133(2, 3, 3, n0)
                    else:
                        return
            else:
                return
    else:
        return


def func133(a1, b1, i1, n0):
    if i1 < n0:
        if a1 % 2:
            yield [a1]
            yield from func163(b1, a1, n0, i1)
        else:
            if (i1 + 1) < n0:
                if b1 % 2:
                    yield [b1]
                    yield from func163(a1 + b1, b1, n0, i1 + 1)
                else:
                    if ((i1 + 1) + 1) < n0:
                        if (a1 + b1) % 2:
                            yield [a1 + b1]
                            yield from func163(
                                b1 + (a1 + b1), a1 + b1, n0, (i1 + 1) + 1
                            )
                        else:
                            yield from func133(
                                b1 + (a1 + b1),
                                (a1 + b1) + (b1 + (a1 + b1)),
                                ((i1 + 1) + 1) + 1,
                                n0,
                            )
                    else:
                        return
            else:
                return
    else:
        return


def func163(b1, a1, n0, i1):
    if (i1 + 1) < n0:
        if b1 % 2:
            yield [b1]
            yield from func163(a1 + b1, b1, n0, i1 + 1)
        else:
            if ((i1 + 1) + 1) < n0:
                if (a1 + b1) % 2:
                    yield [a1 + b1]
                    yield from func163(b1 + (a1 + b1), a1 + b1, n0, (i1 + 1) + 1)
                else:
                    yield from func133(
                        b1 + (a1 + b1),
                        (a1 + b1) + (b1 + (a1 + b1)),
                        ((i1 + 1) + 1) + 1,
                        n0,
                    )
            else:
                return
    else:
        return


inst = func101(50)
for _ in range(20):
    print(next(inst))
