"""
Test Generator

Cleanup files: `git clean -dfX`
"""

from python2verilog.frontend import GeneratorParser
import unittest
import os
import warnings
import ast
import csv
import configparser
import subprocess


class TestGeneratorParser(unittest.TestCase):
    def run_test(self, function_name, TEST_CASE, dir="data/generator/"):
        # TODO: remove nested with statements

        # Get config from path
        ABS_PATH = os.path.join(
            os.path.dirname(os.path.abspath(__file__)), dir, function_name
        )

        config = configparser.ConfigParser()
        config.read(os.path.join(ABS_PATH, "config.ini"))
        DIR_OF_ABS_PATH = {
            key: os.path.join(ABS_PATH, value)
            for key, value in config["file_names"].items()
        }

        with open(DIR_OF_ABS_PATH["generator"]) as python_file:
            python = python_file.read()
            _locals = dict()
            exec(python, None, _locals)  # grab's exec's populated scoped variables

            tree = ast.parse(python)

            with open(DIR_OF_ABS_PATH["expected"], mode="w") as expected_file:
                generator_inst = _locals[function_name](*TEST_CASE)
                for tupl in generator_inst:
                    expected_file.write(str(tupl)[1:-1] + "\n")

            with open(DIR_OF_ABS_PATH["visual"], mode="w") as visual_file:
                generator_inst = _locals[function_name](*TEST_CASE)

                WIDTH, HEIGHT = 100, 100
                matrix = [["." for x in range(WIDTH)] for y in range(HEIGHT)]
                for tupl in generator_inst:
                    matrix[tupl[0]][tupl[1]] = "@"
                for row in matrix:
                    for elem in row:
                        visual_file.write(elem)
                    visual_file.write("\n")

            with open(DIR_OF_ABS_PATH["ast_dump"], mode="w") as ast_dump_file:
                ast_dump_file.write(ast.dump(tree, indent="  "))

            with open(DIR_OF_ABS_PATH["module"], mode="w") as module_file:
                func = tree.body[0]
                genParser = GeneratorParser(func)
                module_file.write(str(genParser.generate_verilog()))

            with open(DIR_OF_ABS_PATH["testbench"], mode="w") as testbench_file:
                text = f"module {function_name}"

                text += """_tb;
  // Inputs
  reg _clock;
  reg _start;
"""  # TODO: use the NAMED_FUNCTION constant instead of generator
                for i, v in enumerate(tree.body[0].args.args):
                    text += f"  reg signed [31:0] {v.arg};\n"
                text += "\n  // Outputs\n"
                for i in range(len(tree.body[0].returns.slice.elts)):
                    text += f"  wire signed [31:0] _out{i};\n"

                text += """
  wire _done;

  // Instantiate the module under test
  """
                text += function_name

                text += """ dut (
    ._clock(_clock),
    ._start(_start),
"""
                for i, v in enumerate(tree.body[0].args.args):
                    text += f"    .{v.arg}({v.arg}),\n"
                for i in range(len(tree.body[0].returns.slice.elts)):
                    text += f"    ._out{i}(_out{i}),\n"
                text += """
    ._done(_done)
  );

  // Clock generation
  always #5 _clock = !_clock;

  // Stimulus
  initial begin
    // Initialize inputs
    _start = 0;
"""

                for i, v in enumerate(tree.body[0].args.args):
                    text += f"    {v.arg} = {TEST_CASE[i]};\n"
                text += """
    _clock = 0;

    // Wait for a few clock cycles
    #10;

    // Start the drawing process
    @(posedge _clock);
    _start = 1;

    // Wait for the drawing to complete
    repeat (100) begin
      @(posedge _clock);
      _start = 0;
      // Display the outputs for every cycle after start
      $display(\""""  # TODO: use NAMED_FUNCTION instead of "generator dut"

                text += "%0d, " * (len(tree.body[0].returns.slice.elts) - 1)
                text += """%0d\""""

                for i in range(len(tree.body[0].returns.slice.elts)):
                    text += f", _out{i}"

                text += ");\n"

                text += """
    end

    // Finish simulation
    $finish;
  end

endmodule
"""

                testbench_file.write(text)

            if os.path.exists(DIR_OF_ABS_PATH["actual"]):
                os.remove(DIR_OF_ABS_PATH["actual"])

            iverilog_cmd = f"iverilog -s {function_name}_tb {DIR_OF_ABS_PATH['module']} {DIR_OF_ABS_PATH['testbench']} && unbuffer vvp a.out >> {DIR_OF_ABS_PATH['actual']}\n"
            self.assertEqual(
                subprocess.run(
                    iverilog_cmd, shell=True, capture_output=True, text=True
                ).stderr,
                "",
            )

            with open(DIR_OF_ABS_PATH["actual"]) as act_f:
                with open(DIR_OF_ABS_PATH["expected"]) as exp_f:
                    expected = csv.reader(exp_f)
                    actual = csv.reader(act_f)

                    actual_coords = set()
                    expected_coords = set()

                    for row in actual:
                        valid = True
                        for element in row:
                            if element.strip() == "x":
                                valid = False
                        if valid:
                            actual_coords.add(tuple(row))

                    for row in expected:
                        expected_coords.add(tuple(row))

                    self.assertEqual(
                        actual_coords - expected_coords,
                        set(),
                        f"Extra coordinates: {str(actual_coords - expected_coords)} {str(actual_coords)} {str(expected_coords)}",
                    )
                    self.assertEqual(
                        expected_coords - actual_coords,
                        set(),
                        f"Missing Coordinates: {str(expected_coords - actual_coords)} {str(actual_coords)} {str(expected_coords)}",
                    )

                    return "Running test"

    def test_rectangle_filled(self):
        self.run_test("rectangle_filled", (23, 17, 5, 7))

    def test_circle_lines(self):
        self.run_test("circle_lines", (23, 17, 5))

    def test_rectangle_lines(self):
        self.run_test("rectangle_lines", (23, 17, 5, 7))

    def test_defaults(self):
        self.run_test("defaults", (1, 2, 3, 4))
