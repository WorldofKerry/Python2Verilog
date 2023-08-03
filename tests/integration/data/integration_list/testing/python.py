def testing(n) -> tuple[int]:
    # x = 0
    # y = 15
    # d = 3 - 2 * 15
    # while y >= x:
    #     x = x + 1
    #     if d > 0:
    #         y = y - 1
    #         # d = d + 4 * (x - y) + 10
    #     else:
    #         d = d + 4 * x + 6
    #     yield (x,)

    i = 0
    yield (i,)
    while i < n:
        if 1:
            i += 1
            yield (i,)
        else:
            i += 2
