def rectangle_lines(s_x, s_y, height, width) -> tuple[int, int]:
    i0 = 0
    while i0 < width:
        yield (s_x, s_y + i0)
        yield (s_x + height - 1, s_y + i0)
        i0 += 1

    i1 = 0
    while i1 < height:
        yield (s_x + i1, s_y)
        yield (s_x + i1, s_y + width - 1)
        i1 += 1
