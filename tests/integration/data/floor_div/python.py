def floor_div(n) -> tuple[int]:
    i = 1
    while i < n:
        j = 1
        while j < n:
            result = i // j
            yield result
            j += 1
        i += 1
