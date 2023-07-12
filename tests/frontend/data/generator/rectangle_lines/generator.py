def rectangle_lines(s_x, s_y, height, width) -> tuple[int, int]:
    for i0 in range(0, width):
        yield (s_x, s_y + i0)
        yield (s_x + height - 1, s_y + i0)

    for i1 in range(height):
        yield (s_x + i1, s_y)
        yield (s_x + i1, s_y + width - 1)
