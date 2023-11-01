def func128(a1, b1, i1, n0):
    if i1 < n0:
        if a1 % 2:
            yield [a1]
            yield from func153(n0, a1, b1, i1)
        else:
            if (i1 + 1) < n0:
                if b1 % 2:
                    yield [b1]
                    yield from func153(n0, b1, a1 + b1, i1 + 1)
                else:
                    yield from func128(a1 + b1, b1 + (a1 + b1), (i1 + 1) + 1, n0)
            else:
                return
    else:
        return


def func101(n0):
    if 0 < n0:
        if 0:
            yield [0]
            yield from func153(n0, 0, 1, 0)
        else:
            if 1 < n0:
                if 1:
                    yield [1]
                    yield from func153(n0, 1, 1, 1)
                else:
                    yield from func128(1, 2, 2, n0)
            else:
                return
    else:
        return


def func153(n0, a1, b1, i1):
    if (i1 + 1) < n0:
        if b1 % 2:
            yield [b1]
            yield from func153(n0, b1, a1 + b1, i1 + 1)
        else:
            yield from func128(a1 + b1, b1 + (a1 + b1), (i1 + 1) + 1, n0)
    else:
        return


inst = func101(50)
for _ in range(20):
    print(next(inst))
