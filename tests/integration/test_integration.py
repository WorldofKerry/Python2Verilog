import unittest
import ast
import warnings
import os
import configparser
import subprocess
import csv

from python2verilog.backend.verilog import Verilog
from python2verilog.frontend import PythonParser
from python2verilog.utils.visualization import make_visual


class TestMain(unittest.TestCase):
    def run_test(self, function_name, test_cases, dir="data/integration/"):
        assert len(test_cases) > 0, "Please include at least one test case"
        assert len(test_cases[0]) > 0, "Please have data in the test case"

        ABS_DIR = os.path.join(
            os.path.dirname(os.path.abspath(__file__)), dir, function_name
        )

        assert os.path.exists(
            ABS_DIR
        ), f"Test on `{ABS_DIR}` failed, as that directory does not exist"

        config = configparser.ConfigParser()
        config.read(os.path.join(ABS_DIR, "config.ini"))
        FILES_IN_ABS_DIR = {
            key: os.path.join(ABS_DIR, value)
            for key, value in config["file_names"].items()
        }

        with open(FILES_IN_ABS_DIR["python"]) as python_file:
            python = python_file.read()
            _locals = dict()
            exec(python, None, _locals)  # grab's exec's populated scoped variables

            tree = ast.parse(python)

            with open(FILES_IN_ABS_DIR["expected"], mode="w") as expected_file:
                for test_case in test_cases:
                    generator_inst = _locals[function_name](*test_case)
                    size = None
                    for tupl in generator_inst:
                        if size is None:
                            size = len(tupl)
                        else:
                            assert (
                                len(tupl) == size
                            ), f"All generator yields must be same length tuple, but got {tupl} of length {len(tupl)} when previous yields had length {size}"
                        for e in tupl:
                            assert isinstance(e, int)
                        expected_file.write(
                            " " + str(tupl)[1:-1] + "\n"
                        )  # Verilog row elements have a space prefix

            make_visual(
                _locals[function_name](*test_cases[0]),
                FILES_IN_ABS_DIR["expected_visual"],
            )

            with open(FILES_IN_ABS_DIR["ast_dump"], mode="w") as ast_dump_file:
                ast_dump_file.write(ast.dump(tree, indent="  "))

            with open(FILES_IN_ABS_DIR["module"], mode="w") as module_file:
                function = tree.body[0]
                ir_generator = PythonParser(function)
                output = ir_generator.parse_statements(function.body, "")
                # warnings.warn(output.to_lines())
                verilog = Verilog()
                verilog.from_ir(output, ir_generator.global_vars)
                verilog.setup_from_python(function)
                module_file.write(verilog.get_module().to_string())

            with open(FILES_IN_ABS_DIR["testbench"], mode="w") as testbench_file:
                testbench_file.write(
                    verilog.get_testbench_improved(test_cases).to_lines().to_string()
                )

            open(FILES_IN_ABS_DIR["actual"], mode="w+")

            iverilog_cmd = f"iverilog -s {function_name}_tb {FILES_IN_ABS_DIR['module']} {FILES_IN_ABS_DIR['testbench']} -o iverilog.log && unbuffer vvp iverilog.log >> {FILES_IN_ABS_DIR['actual']} && rm iverilog.log\n"
            output = subprocess.run(
                iverilog_cmd, shell=True, capture_output=True, text=True
            )
            if output.stderr != "" or output.stdout != "":
                warnings.warn(
                    f"ERROR with running verilog simulation on {function_name}, with: {output.stderr} {output.stdout}"
                )

            with open(FILES_IN_ABS_DIR["actual"], mode="r") as act_f:
                with open(FILES_IN_ABS_DIR["filtered_actual"], mode="w") as filtered_f:
                    raw = csv.reader(act_f)
                    filtered = []
                    for row in raw:
                        if row[0].strip() == "1":
                            tupl = tuple([int(e) for e in row[1:]])
                            filtered.append(tupl)
                            filtered_f.write(" " + str(tupl)[1:-1] + "\n")

                    make_visual(filtered, FILES_IN_ABS_DIR["actual_visual"])

            with open(FILES_IN_ABS_DIR["actual"]) as act_f:
                with open(FILES_IN_ABS_DIR["expected"]) as exp_f:
                    expected = csv.reader(exp_f)
                    actual = csv.reader(act_f)

                    actual_coords = set()
                    expected_coords = set()

                    for row in actual:
                        if row[0].strip() == "1":  # First bit is valid bit
                            actual_coords.add(tuple(row[1:]))

                    for row in expected:
                        expected_coords.add(tuple(row))

                    self.assertEqual(
                        actual_coords - expected_coords,
                        set(),
                        f"str(actual_coords - expected_coords) <-- extra coordinates, all: {str(actual_coords)} {str(expected_coords)}",
                    )
                    self.assertEqual(
                        expected_coords - actual_coords,
                        set(),
                        f"str(expected_coords - actual_coor <-- missing coordinates, all: {str(actual_coords)} {str(expected_coords)}",
                    )

                    return "Running test"

    def test_defaults(self):
        self.run_test("defaults", [(1, 2, 3, 4), (13, 45, 11, 17)])

    def test_circle_lines(self):
        self.run_test("circle_lines", [(21, 37, 13), (8, 3, 4)])

    def test_happy_face(self):
        self.run_test("happy_face", [(50, 50, 40), (32, 44, 13)])

    def test_rectangle_filled(self):
        self.run_test("rectangle_filled", [(32, 84, 12, 15)])

    def test_rectangle_lines(self):
        self.run_test("rectangle_lines", [(32, 84, 12, 15)])
