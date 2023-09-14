def testing(n) -> tuple[int]:
    yield n, 1
    a = n
    b = a * 3
    if b == a:
        c = b
    else:
        c = n + 1
    yield c, 2
    d = a * 4 * 3
    c = a * 4 + 7
    yield d, c
