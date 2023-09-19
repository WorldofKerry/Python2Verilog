def circle_lines(s_x, s_y, height):
    x = 0
    y = height
    d = 3 - 2 * y
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
        yield (s_x + x, s_y + y)
        yield (s_x + x, s_y - y)
        yield (s_x - x, s_y + y)
        yield (s_x - x, s_y - y)
        yield (s_x + y, s_y + x)
        yield (s_x + y, s_y - x)
        yield (s_x - y, s_y + x)
        yield (s_x - y, s_y - x)


def fib(n: int):
    a = 0
    b = 1
    c = 0
    count = 1
    while count < n:
        count += 1
        a = b
        b = c
        c = a + b
        yield c


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
    yield x, y, x + y
    yield x, y, x - y
    yield x, y, x * y
    # yield x, y, x / y
    if y != 0:
        yield (x, y, x // y)
        yield (x, y, x % y)
    # yield x, y, x**y  #

    # Comparison operators
    # yield x, y, x == y
    # yield x, y, x != y
    # yield x, y, x < y
    # yield x, y, x > y
    # yield x, y, x <= y
    # yield x, y, x >= y

    # # Logical operators
    # yield x, y, x and y
    # yield x, y, x or y
    # yield x, y, not x

    # # Bitwise operators
    # yield x, y, x & y
    # yield x, y, x | y
    # yield x, y, x ^ y
    # yield x, y, ~x
    # yield x, y, x << y
    # yield x, y, x >> y

    # # Assignment operators
    # z = x
    # yield x, y, z
    # z += y
    # yield x, y, z
    # z -= y
    # yield x, y, z
    # z *= y
    # yield x, y, z
    # z /= y
    # yield x, y, z
    # z //= y
    # yield x, y, z
    # z %= y
    # yield x, y, z
    # z **= y
    # yield x, y, z
    # z &= y
    # yield x, y, z
    # z |= y
    # yield x, y, z
    # z ^= y
    # yield x, y, z
    # z <<= y
    # yield x, y, z
    # z >>= y
    # yield x, y, z

    # # Identity and membership operators
    # yield x, y, x is y
    # yield x, y, x is not y
    # yield x, y, x in [y, z]
    # yield x, y, x not in [y, z]


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
