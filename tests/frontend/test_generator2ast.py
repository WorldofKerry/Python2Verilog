from python2verilog.frontend import Generator2Ast
import unittest
import ast
import warnings


class TestGenerator2Ast(unittest.TestCase):
    def test_all(self):
        func = """
def circle_lines(s_x, s_y, height) -> tuple[int, int]:
    a = 123
    yield(a, height)
    s_y = a
    yield(s_x, s_y)
        """
        tree = ast.parse(func)
        with open("ast.log", mode="w") as ast_file:
            ast_file.write(ast.dump(tree, indent="  "))
        generatorParser = Generator2Ast(tree.body[0])

        with open("module.log", mode="w") as module_file:
            module_file.write(generatorParser.generate_verilog().to_string())
        warnings.warn((generatorParser.generate_verilog()))
