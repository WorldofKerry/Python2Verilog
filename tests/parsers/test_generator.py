from python2verilog.parsers import GeneratorParser
import unittest
import os
import inspect
import warnings
import ast
import csv
import configparser


class TestGeneratorParser(unittest.TestCase):
    def run_test(self, name, TEST_CASE, dir="data/generator/"):
        # Get config from path
        PATH_TO_TEST = os.path.join(
            os.path.dirname(os.path.abspath(__file__)), dir, name
        )

        config = configparser.ConfigParser()
        config.read(os.path.join(PATH_TO_TEST, "config.ini"))

        FULL_PATH = PATH_TO_TEST
        PYTHON_GENERATOR_FILENAME = config["file_names"]["generator"]
        NAMED_FUNCTION = config["file_names"]["test_name"]
        EXPECTED_FILENAME = config["file_names"]["expected"]
        ACTUAL_FILENAME = config["file_names"]["actual"]
        MODULE_FILENAME = config["file_names"]["module"]
        TESTBENCH_FILENAME = config["file_names"]["testbench"]

        with open(os.path.join(FULL_PATH, PYTHON_GENERATOR_FILENAME)) as python_file:
            python = python_file.read()
            _locals = dict()
            exec(python, None, _locals)  # grab's exec's populated scoped variables

            tree = ast.parse(python)
            generator_inst = _locals[NAMED_FUNCTION](*TEST_CASE)

            with open(
                os.path.join(FULL_PATH, EXPECTED_FILENAME), mode="w"
            ) as expected_file:
                for tupl in generator_inst:
                    expected_file.write(str(tupl)[1:-1] + "\n")

            with open(
                os.path.join(FULL_PATH, MODULE_FILENAME), mode="w"
            ) as module_file:
                func = tree.body[0]
                genParser = GeneratorParser(func)
                module_file.write(str(genParser.generate_verilog()))

            with open(
                os.path.join(FULL_PATH, TESTBENCH_FILENAME), mode="w"
            ) as testbench_file:
                text = """module generator_tb;
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
                text += NAMED_FUNCTION
                
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

                # a = 23;
                # b = 17;
                # c = 5;
                # d = 0;
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

                try:
                    with open(os.path.join(FULL_PATH, ACTUAL_FILENAME), mode="x"):
                        return ""
                except FileExistsError:
                    with open(os.path.join(FULL_PATH, ACTUAL_FILENAME)) as act_f:
                        if (
                            os.path.getsize(os.path.join(FULL_PATH, ACTUAL_FILENAME))
                            == 0
                        ):
                            warnings.warn(f"Skipping, due to empty {os.path.join(FULL_PATH, ACTUAL_FILENAME)}")
                            return

                        with open(os.path.join(FULL_PATH, EXPECTED_FILENAME)) as exp_f:
                            expected = csv.reader(exp_f)
                            actual = csv.reader(act_f)

                            actual_coords = set()
                            expected_coords = set()

                            # TODO: cleanup
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