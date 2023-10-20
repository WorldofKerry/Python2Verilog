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


def fib(n: int) -> int:
    """
    Fibonacci sequence
    """
    a, b = 0, 1
    for count in p2vrange(0, n, 1):
        yield a
        a, b = b, a + b


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


def multiplier_generator(multiplicand: int, multiplier: int) -> int:
    product = 0
    count = 0
    while count < multiplier:
        product += multiplicand
        count += 1
    yield product


def operators(x, y):
    yield 0, x
    yield 1, y

    # Arithmetic operators
    yield 2, x + y
    yield 3, x - y
    yield 4, x * y
    # yield x / y

    if y != 0:
        yield 5, x // y
        yield 6, x % y
    # yield x**y

    # Comparison operators
    yield 7, x == x
    yield 8, x == -x
    yield 9, x == y
    yield 10, x != y
    yield 11, x < y
    yield 12, x > y
    yield 13, x <= y
    yield 14, x >= y

    yield 88888888, 88888888  # delimiter

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


def p2vrange(start: int, stop: int, step: int) -> int:
    """
    Simplified version of Python's built-in range function
    """
    while start < stop:
        yield start
        start += step


def dupe(base: int, limit: int, step: int) -> int:
    """
    Dupe hrange
    """
    inst = p2vrange(base, limit, step)
    for out in inst:
        yield out
        yield out


def double_for(limit: int) -> tuple[int, int]:
    """
    Double for loop
    """
    x_gen = p2vrange(0, limit, 1)
    for x in x_gen:
        y_gen = p2vrange(0, limit, 1)
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


def keyword_test():
    """
    Testing for break, continue, return
    """
    i = 0
    while i < 10:
        if i % 2 == 0:
            i += 1
            continue
        yield i
        i += 3

    i = 0
    while i < 10:
        if i == 7:
            break
        yield i
        i += 1

    i = 0
    while i < 10:
        if i == 5:
            return
        yield i
        i += 1


def quad_multiply(left, right):
    """
    Given left and right,
    yields
    left * right
    left * -right
    -left * right
    -left * -right
    """
    inst = multiplier_generator(left, right)
    for val in inst:
        yield val
    inst = multiplier_generator(left, -right)
    for val in inst:
        yield val
    inst = multiplier_generator(-left, right)
    for val in inst:
        yield val
    for val in multiplier_generator(-left, -right):
        yield val


def multiplier(multiplicand: int, multiplier: int) -> int:
    product = 0
    while multiplier > 0:
        product += multiplicand
        multiplier -= 1
    return product


def fib_product(n):
    """
    Yields the product of the first n fibonacci numbers
    """
    for num in fib(n):
        prod = multiplier(num, num)
        yield prod
