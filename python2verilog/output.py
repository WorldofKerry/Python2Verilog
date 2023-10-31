def func101(n0):
    i0 = 0
    i1 = 0
    if 0 < n0:
        yield [0]
        yield [1]
        i2 = 2
        i1 = 2
        if 2 < n0:
            yield [2]
            yield [3]
            i2 = 4
            yield from func122(4, n0)
        else:
            return
    else:
        return


def func122(i1, n0):
  if (i1 < n0):
    yield [i1]
    yield [i1 + 1]
    i2 = (i1 + 2)
    i1 = (i1 + 2)
    if ((i1 + 2) < n0):
      yield [i1 + 2]
      yield [(i1 + 2) + 1]
      i2 = ((i1 + 2) + 2)
      yield from func122((i1 + 2) + 2, n0)
    else:
      return
  else:
    return


inst = func101(50)
for _ in range(20):
    print(next(inst))
