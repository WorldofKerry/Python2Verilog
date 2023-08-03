def testing(n) -> tuple[int]:
    # i = 0
    # a = i
    # while i < n:
    #     i = i + 1
    #     a = i + 2
    # yield (i,)

    # i = 0
    # a = 1
    # yield(a,)
    # if n > 10:
    #     yield (1,)
    # else:
    #     yield (2,)
    # yield (3,)

    i = 0
    yield (i,)
    while i < n:
        if 1:
            i += 1
            yield (i,)
        else:
            i += 2

    # i = 0
    # while i < n:
    #     # i = 4
    #     if i > 1:
    #         i += 1
    #         yield (i + 3,)
    #         # i = 7
    #     else:
    #         i += 2
    #         # i = 8
    # yield (i,)

    # a = 0
    # b = 1
    # c = 0
    # count = 1
    # while count < n:
    #     count += 1
    #     a = b
    #     b = c
    #     c = a + b
    #     yield (c,)
