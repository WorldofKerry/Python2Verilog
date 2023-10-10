def circle_lines(centre_x: int, centre_y: int, radius: int) -> tuple[int, int]:
    offset_y = 0
    offset_x = radius
    crit = 1 - radius
    while offset_y <= offset_x:
        yield (centre_x + offset_x, centre_y + offset_y)  # -- octant 1
        yield (centre_x + offset_y, centre_y + offset_x)  # -- octant 2
        yield (centre_x - offset_x, centre_y + offset_y)  # -- octant 4
        yield (centre_x - offset_y, centre_y + offset_x)  # -- octant 3
        yield (centre_x - offset_x, centre_y - offset_y)  # -- octant 5
        yield (centre_x - offset_y, centre_y - offset_x)  # -- octant 6
        yield (centre_x + offset_x, centre_y - offset_y)  # -- octant 8
        yield (centre_x + offset_y, centre_y - offset_x)  # -- octant 7
        offset_y = offset_y + 1
        if crit <= 0:
            crit = crit + 2 * offset_y + 1
        else:
            offset_x = offset_x - 1
            crit = crit + 2 * (offset_y - offset_x) + 1


def fib(n: int):
    """
    Fibonacci sequence
    """
    a, b = 0, 1
    count = 1
    while count < n:
        if a != 21:
            yield a
        a, b = b, a + b
        count = count + 1


def floor_div(n) -> tuple[int]:
    i = 1
    while i < n:
        j = 1
        while j < n:
            yield i // j
            j += 1
        i += 1


def happy_face(s_x, s_y, height):
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
    i, j = 0, 0
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
    i, j = 0, 0
    while i < rectangle_width:
        while j < rectangle_height:
            yield (x + i, y + j)
            j += 1
        j = 0
        i += 1


def multiplier(multiplicand, multiplier):
    product = 0
    count = 0
    while count < multiplier:
        product += multiplicand
        count += 1
    yield product


def operators(x, y):
    # yield 0, 0, 0

    # Arithmetic operators
    yield x + y
    yield x - y
    yield x * y
    # yield x / y
    yield x == x
    yield x == -x
    if y != 0:
        yield (x // y)
        yield (x % y)
    # yield x**y  #

    # Comparison operators
    # yield x == y
    # yield x != y
    # yield x < y
    # yield x > y
    # yield x <= y
    # yield x >= y

    # # Logical operators
    # yield x and y
    # yield x or y
    # yield not x

    # # Bitwise operators
    # yield x & y
    # yield x | y
    # yield x ^ y
    # yield ~x
    # yield x << y
    # yield x >> y

    # # Assignment operators
    # z = x
    # yield z
    # z += y
    # yield z
    # z -= y
    # yield z
    # z *= y
    # yield z
    # z /= y
    # yield z
    # z //= y
    # yield z
    # z %= y
    # yield z
    # z **= y
    # yield z
    # z &= y
    # yield z
    # z |= y
    # yield z
    # z ^= y
    # yield z
    # z <<= y
    # yield z
    # z >>= y
    # yield z

    # # Identity and membership operators
    # yield x is y
    # yield x is not y
    # yield x in [y, z]
    # yield x not in [y, z]


def rectangle_filled(s_x, s_y, height, width):
    i0 = 0
    while i0 < width:
        i1 = 0
        while i1 < height:
            yield (s_x + i1, s_y + i0)
            i1 = i1 + 1
        i0 = i0 + 1


def rectangle_lines(s_x, s_y, height, width):
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


def division(dividend, divisor, precision):
    iter = 0
    if dividend < 0:
        dividend = -dividend
    while dividend > 0 and iter <= precision:
        digit = 0
        while (digit + 1) * divisor <= dividend:
            digit += 1
        yield digit
        dividend -= digit * divisor
        if dividend // divisor == 0:
            dividend *= 10
        iter += 1


def olympic_logo_naive(mid_x, mid_y, radius):
    spread = radius - 2
    gen = circle_lines(mid_x, mid_y + spread, radius)
    for x, y in gen:
        yield x, y, 50
    gen = circle_lines(mid_x + spread * 2, mid_y + spread, radius)
    for x, y in gen:
        yield x, y, 180
    gen = circle_lines(mid_x - spread * 2, mid_y + spread, radius)
    for x, y in gen:
        yield x, y, 500
    gen = circle_lines(mid_x + spread, mid_y - spread, radius)
    for x, y in gen:
        yield x, y, 400
    gen = circle_lines(mid_x - spread, mid_y - spread, radius)
    for x, y in gen:
        yield x, y, 300


def hrange(base: int, step: int, limit: int) -> int:
    """
    Simplified version of Python's built-in range function
    """
    while base < limit:
        yield base
        base += step


def dupe(base: int, step: int, limit: int) -> int:
    """
    Dupe hrange
    """
    inst = hrange(base, step, limit)
    for out in inst:
        yield out
        yield out


def double_for(limit: int) -> tuple[int, int]:
    """
    Double for loop
    """
    x_gen = hrange(0, 1, limit)
    for x in x_gen:
        y_gen = hrange(0, 1, limit)
        for y in y_gen:
            yield x, y


def olympic_logo_mids(mid_x: int, mid_y: int, spread: int) -> tuple[int, int, int]:
    """
    Yields the middle coordinates and the color
    for the 5 circles in the olympics logo
    """
    yield mid_x, mid_y + spread, 50
    yield mid_x + spread * 2, mid_y + spread, 180
    yield mid_x - spread * 2, mid_y + spread, 500
    yield mid_x + spread, mid_y - spread, 400
    yield mid_x - spread, mid_y - spread, 300


def olympic_logo(mid_x, mid_y, radius):
    """
    Draws the olympic logo
    """
    spread = radius - 2
    middles_and_colors = olympic_logo_mids(mid_x, mid_y, spread)
    for x, y, color in middles_and_colors:
        coords = circle_lines(x, y, radius)
        for x, y in coords:
            yield x, y, color
