def circle_lines(s_x, s_y, height) -> tuple[int, int, int, int, int, int]:
    x = 0
    y = height
    d = 3 - 2 * y
    yield (s_x + x, s_y + y, height, x, y, d)
    yield (s_x + x, s_y - y, height, x, y, d)
    yield (s_x - x, s_y + y, height, x, y, d)
    yield (s_x - x, s_y - y, height, x, y, d)
    yield (s_x + y, s_y + x, height, x, y, d)
    yield (s_x + y, s_y - x, height, x, y, d)
    yield (s_x - y, s_y + x, height, x, y, d)
    yield (s_x - y, s_y - x, height, x, y, d)
    while y >= x:
        x = x + 1
        if d > 0:
            y = y - 1
            # d = d + 4 * (x - y) + 10
        else:
            d = d + 4 * x + 6
        yield (s_x + x, s_y + y, height, x, y, d)
        yield (s_x + x, s_y - y, height, x, y, d)
        yield (s_x - x, s_y + y, height, x, y, d)
        yield (s_x - x, s_y - y, height, x, y, d)
        yield (s_x + y, s_y + x, height, x, y, d)
        yield (s_x + y, s_y - x, height, x, y, d)
        yield (s_x - y, s_y + x, height, x, y, d)
        yield (s_x - y, s_y - x, height, x, y, d)
