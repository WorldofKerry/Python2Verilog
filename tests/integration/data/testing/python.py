def testing(n) -> tuple[int]:
    i = 0
    while i < n:
        i += 1
    yield i
    yield i + 1
