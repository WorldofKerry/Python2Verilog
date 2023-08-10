def operators(low, high) -> tuple[int, int, int]:
    x = low
    while x < high:
        y = low
        while y < high:
            # Arithmetic operators
            yield (x, y, x + y)
            yield (x, y, x - y)
            yield (x, y, x * y)
            # yield x, y, x / y
            if y != 0:
                yield (x, y, x // y)
                yield (x, y, x % y)
            # yield x, y, x**y
            y += 1
        x += 1

        # # Comparison operators
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
