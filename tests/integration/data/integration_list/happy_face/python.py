def happy_face(s_x, s_y, height) -> tuple[int, int]:
    # Generate points for the outer circle
    x = 0
    y = height
    d = 3 - 2 * height
    yield (s_x + x, s_y + y)
    yield (s_x + x, s_y - y)
    yield (s_x - x, s_y + y)
    yield (s_x - x, s_y - y)
    yield (s_x + y, s_y + x)
    yield (s_x + y, s_y - x)
    yield (s_x - y, s_y + x)
    yield (s_x - y, s_y - x)
    while y >= x:
        x = x + 1
        if d > 0:
            y = y - 1
            d = d + 4 * (x - y) + 10
        else:
            d = d + 4 * x + 6
        # yield (x, y, d)
        yield (s_x + x, s_y + y)
        yield (s_x + x, s_y - y)
        yield (s_x - x, s_y + y)
        yield (s_x - x, s_y - y)
        yield (s_x + y, s_y + x)
        yield (s_x + y, s_y - x)
        yield (s_x - y, s_y + x)
        yield (s_x - y, s_y - x)

    # Generate points for the eyes
    rectangle_width = height // 3
    rectangle_height = height // 3

    # Left eye
    x = s_x + 10
    y = s_y + 5

    # Rectangle
    i = 0
    j = 0
    while i < rectangle_width:
        while j < rectangle_height:
            yield (x + i, y + j)
            j += 1
        j = 0
        i += 1

    # Right eye
    x = s_x - 10
    y = s_y + 5

    # Rectangle
    i = 0
    j = 0
    while i < rectangle_width:
        while j < rectangle_height:
            yield (x + i, y + j)
            j += 1
        j = 0
        i += 1
