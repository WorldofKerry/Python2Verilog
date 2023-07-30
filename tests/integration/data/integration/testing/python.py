def testing(n) -> tuple[int]:
    i = 0
    a = i
    while i < n:
        i = i + 1
        a = i + 2
    yield (i,)
    # i = 0
    # a = 1
    # yield(a,)
