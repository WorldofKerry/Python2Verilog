import unittest
import ast
import warnings
import os
import configparser
import subprocess
import csv
import pytest
import statistics

from python2verilog.backend.verilog import Verilog
from python2verilog.frontend import GeneratorParser
from python2verilog.optimizer import optimizer
from python2verilog.convert import convert
from python2verilog.utils.visualization import make_visual


@pytest.mark.usefixtures("argparse")
class TestMain(unittest.TestCase):
    def run_test(self, function_name, test_cases, dir="data/integration/"):
        """
        Stats will only be gathered on the last test
        """

        assert len(test_cases) > 0, "Please include at least one test case"

        for test_case in test_cases:
            assert isinstance(
                test_case, tuple
            ), "Inputs should be tuples, use (x,) for single-width tuple"
            assert len(test_case) > 0, "Please have data in the test case"

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
                        assert isinstance(
                            tupl, tuple
                        ), "Yield tuples only, use (x,) for single-width tuples"
                        if size is None:
                            size = len(tupl)
                        else:
                            assert (
                                len(tupl) == size
                            ), f"All generator yields must be same length tuple, but got {tupl} of length {len(tupl)} when previous yields had length {size}"
                        for e in tupl:
                            assert isinstance(e, int)
                        if len(tupl) > 1:
                            expected_file.write(f"{str(tupl)[1:-1]}\n")
                        else:
                            expected_file.write(
                                f"{str(tupl)[1:-2]}\n"
                            )  # remove trailing comma

            make_visual(
                _locals[function_name](*test_cases[0]),
                FILES_IN_ABS_DIR["expected_visual"],
            )

            with open(FILES_IN_ABS_DIR["ast_dump"], mode="w") as ast_dump_file:
                ast_dump_file.write(ast.dump(tree, indent="  "))

            with open(FILES_IN_ABS_DIR["module"], mode="w") as module_file:
                function = tree.body[0]
                verilog = convert(function, 3)
                module_file.write(verilog.get_module().to_string())

            with open(FILES_IN_ABS_DIR["testbench"], mode="w") as testbench_file:
                testbench_file.write(
                    verilog.get_testbench(test_cases).to_lines().to_string()
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
                            actual_coords.add(tuple([e.strip() for e in row[1:]]))

                    for row in expected:
                        expected_coords.add(tuple([e.strip() for e in row]))

                    self.assertEqual(
                        actual_coords - expected_coords,
                        set(),
                        f"str(actual_coords - expected_coords) <-- extra coordinates, actual expected: {str(actual_coords)} {str(expected_coords)}",
                    )
                    self.assertEqual(
                        expected_coords - actual_coords,
                        set(),
                        f"str(expected_coords - actual_coor <-- missing coordinates, actual expected: {str(actual_coords)} {str(expected_coords)}",
                    )

                    return "Running test"

    @staticmethod
    def filter_tests(test_cases: list[tuple], args: dict):
        """
        Filters tests based on pytest args
        """
        if args.first_test:
            return [test_cases[0]]
        return test_cases

    def test_circle_lines(self):
        test_cases = [(21, 37, 7), (89, 45, 43)]
        self.run_test("circle_lines", self.filter_tests(test_cases, self.args))

    def test_happy_face(self):
        test_cases = [(50, 51, 7), (86, 97, 43)]
        self.run_test("happy_face", self.filter_tests(test_cases, self.args))

    def test_rectangle_filled(self):
        test_cases = [(32, 84, 5, 7), (64, 78, 34, 48)]
        self.run_test("rectangle_filled", self.filter_tests(test_cases, self.args))

    def test_rectangle_lines(self):
        test_cases = [(32, 84, 5, 7), (84, 96, 46, 89)]
        self.run_test("rectangle_lines", self.filter_tests(test_cases, self.args))

    def test_fib(self):
        test_cases = [(10,), (35,)]
        self.run_test("fib", self.filter_tests(test_cases, self.args))

    # def test_tree_bfs(self):
    #     binary_tree = [1, 7, 8, 2, 4, 6, 8, 6, 9]
    #     self.run_test(
    #         "tree_bfs", [(binary_tree, [420] * len(binary_tree), len(binary_tree))]
    #     )
