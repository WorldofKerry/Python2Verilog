def func101(n0):
    a0 = 0
    b0 = 1
    i0 = 0
    if i1 < n0:
        if a1 % 2:
            a4 = a1 + 10
            yield {a4}
            yield from func144(a4, i1, b1, n0)
        else:
            a3 = b1
            b2 = a2 + b1
            i3 = i1 + 1
            if i1 < n0:
                if a1 % 2:
                    a4 = a1 + 10
                    yield {a4}
                    yield from func144(a4, i1, b1, n0)
                else:
                    yield from func127(a1, b1, i1, n0)
            else:
                return
    else:
        return


inst = func101(50)
for _ in range(20):
    print(next(inst))
