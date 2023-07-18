def rectangle_filled(s_x, s_y, height, width) -> tuple[int, int]:
    i0 = 0
    while i0 < width:
        i1 = 0
        while i1 < height:
            yield (s_x + i1, s_y + i0)
            i1 = i1 + 1
        i0 = i0 + 1
