def circle_lines(s_x, s_y, height) -> tuple[int, int]:
    x = 0
    y = height
    d = 3 - 2 * height
    # yield (s_x + x, s_y + y)
    # yield (s_x + x, s_y - y)
    # yield (s_x - x, s_y + y)
    # yield (s_x - x, s_y - y)
    # yield (s_x + y, s_y + x)
    # yield (s_x + y, s_y - x)
    # yield (s_x - y, s_y + x)
    # yield (s_x - y, s_y - x)
    while y >= x:
        x = x + 1
        if d > 0:
            y = y - 1
            d = d + 4 * (x - y) + 10
        else:
            d = d + 4 * x + 6
        yield (x, y, d)
        # yield (s_x + x, s_y + y)
        # yield (s_x + x, s_y - y)
        # yield (s_x - x, s_y + y)
        # yield (s_x - x, s_y - y)
        # yield (s_x + y, s_y + x)
        # yield (s_x + y, s_y - x)
        # yield (s_x - y, s_y + x)
        # yield (s_x - y, s_y - x)
