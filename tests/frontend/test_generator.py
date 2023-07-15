"""
Test Generator

Cleanup files: `git clean -dfX`
"""

from python2verilog.frontend import Generator2Ast as GeneratorParser
import unittest
import os
import warnings
import ast
import csv
import configparser
import subprocess


def make_visual(generator_inst, dir: str):
    """
    Any iterable of tuples where the tuples are of length > 0 will work.
    Visualizes the first 3 elements of each tuple as (x, y, colour)
    """
    import numpy as np
    import matplotlib.pyplot as plt

    # Generate the data using the generator function
    data_triple = []

    for yields in generator_inst:
        if len(yields) >= 3:
            data_triple.append(yields[:3])
        elif len(yields) >= 2:
            data_triple.append((*yields[:2], 1))
        else:
            data_triple.append((yields[0], 1, 2))

    data_triple = np.array(data_triple)

    height = max(data_triple[:, 0])
    width = max(data_triple[:, 1])
    # warnings.warn(f"{height}, {width}, {data_triple}")
    grid = np.zeros((int(height) + 1, int(width) + 1))
    for x, y, c in data_triple:
        grid[x, y] = c

    # Create the pixel-like plot
    plt.imshow(grid)

    # Set labels and title
    plt.xlabel("X")
    plt.ylabel("Y")
    plt.title("Pixel-like Plot")

    # Add color bar
    cbar = plt.colorbar()
    cbar.set_label("Z")

    plt.gca().invert_yaxis()

    # Show the plot
    # plt.show()
    plt.savefig(dir)


class TestGeneratorParser(unittest.TestCase):
    def run_test(self, function_name, TEST_CASE, dir="data/generator/"):
        # TODO: remove nested with statements

        # Get config from path
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
                generator_inst = _locals[function_name](*TEST_CASE)
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
                _locals[function_name](*TEST_CASE), FILES_IN_ABS_DIR["expected_visual"]
            )

            with open(FILES_IN_ABS_DIR["ast_dump"], mode="w") as ast_dump_file:
                ast_dump_file.write(ast.dump(tree, indent="  "))

            with open(FILES_IN_ABS_DIR["module"], mode="w") as module_file:
                func = tree.body[0]
                genParser = GeneratorParser(func)
                module_file.write(str(genParser.generate_verilog()))

            with open(FILES_IN_ABS_DIR["testbench"], mode="w") as testbench_file:
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
  wire _valid;

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
    ._done(_done),
    ._valid(_valid)
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
    @(posedge _clock);

    // Wait for the drawing to complete
    while (!_done) begin
      @(posedge _clock);
      _start = 0;
      // Display the outputs for every cycle after start
      $display(\"%0d, """  # TODO: use NAMED_FUNCTION instead of "generator dut"

                text += "%0d, " * (len(tree.body[0].returns.slice.elts) - 1)
                text += """%0d\", _valid"""

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

            open(FILES_IN_ABS_DIR["actual"], mode="w+")

            iverilog_cmd = f"iverilog -s {function_name}_tb {FILES_IN_ABS_DIR['module']} {FILES_IN_ABS_DIR['testbench']} -o iverilog.log && unbuffer vvp iverilog.log >> {FILES_IN_ABS_DIR['actual']} && rm iverilog.log\n"
            output = subprocess.run(
                iverilog_cmd, shell=True, capture_output=True, text=True
            )
            if output != "":
                warnings.warn(
                    f"ERROR with running verilog simulation on {function_name}, with stderr: {output.stderr}"
                )

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
                        f"Extra coordinates: {str(actual_coords - expected_coords)} {str(actual_coords)} {str(expected_coords)}",
                    )
                    self.assertEqual(
                        expected_coords - actual_coords,
                        set(),
                        f"Missing Coordinates: {str(expected_coords - actual_coords)} {str(actual_coords)} {str(expected_coords)}",
                    )

                    return "Running test"

    # def test_rectangle_filled(self):
    # self.run_test("rectangle_filled", (23, 17, 5, 7))

    def test_circle_lines(self):
        self.run_test("circle_lines", (23, 17, 5))

    # def test_rectangle_lines(self):
    # self.run_test("rectangle_lines", (23, 17, 5, 7))

    def test_rectangle_filled_while(self):
        self.run_test("rectangle_filled_while", (23, 17, 5, 7))
