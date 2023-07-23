def testing(n) -> tuple[int, int]:
    i = 0
    while i < n:
        i = i + 1
        j = 0
        while j < n:
            j = j + 1
            yield (i, j)
