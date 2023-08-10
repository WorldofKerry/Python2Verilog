def operators(x, y) -> tuple[int]:
    # Arithmetic operators
    yield x + y
    yield x - y
    yield x * y
    # yield x / y
    yield x // y
    yield x % y
    yield x**y

    # # Comparison operators
    yield x == y
    yield x != y
    yield x < y
    yield x > y
    yield x <= y
    yield x >= y

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
