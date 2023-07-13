# class TestSuper:
#     def __init_subclass__(cls, *args) -> None:
#         print("args", args)


# class TestChild(TestSuper):
#     pass
#     # def __init__(self, var):
#     #     self.var = var


# child = TestChild()


# class A:
#     def __init__(self, x):
#         print("__init__ is called in A")
#         self.x = x


# class B:
#     def __init__(self, *args, **kwargs):
#         print("__init__ is called in B")
#         super().__init__(*args, **kwargs)


# class AB(B, A):
#     def __init__(self, *args, **kwargs):
#         print("__init__ is called in AB")
#         super().__init__(*args, **kwargs)


# ab = AB(123)

from python2verilog.frontend.generator import GeneratorParser
import ast

func = """
def circle_lines(s_x, s_y, height) -> tuple[int, int]:
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
        yield (s_x + x, s_y + y)
        yield (s_x + x, s_y - y)
        yield (s_x - x, s_y + y)
        yield (s_x - x, s_y - y)
        yield (s_x + y, s_y + x)
        yield (s_x + y, s_y - x)
        yield (s_x - y, s_y + x)
        yield (s_x - y, s_y - x)
"""
generatorParser = GeneratorParser(ast.parse(func).body[0])
print(generatorParser.generate_verilog())


class A:
    def __init__(self, x):
        print("__init__ is called in A")
        self.x = x


class B:
    def __init__(self, *args, **kwargs):
        print("__init__ is called in B")
        super().__init__(*args, **kwargs)


class AB(B, A):
    def __init__(self, *args, **kwargs):
        print("__init__ is called in AB")
        super().__init__(*args, **kwargs)


ab = AB(123)
