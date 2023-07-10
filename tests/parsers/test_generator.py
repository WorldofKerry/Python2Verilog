from python2verilog.parsers import GeneratorParser
import unittest
import os
import inspect
import warnings
import ast
import csv

THIS_DIR = os.path.dirname(os.path.abspath(__file__))
NAMED_FUNCTION = "generator" # Default function name in generator.py
PYTHON_GENERATOR_FILENAME = "generator.py"
EXPECTED_FILENAME = "expected.csv"
ACTUAL_FILENAME = "actual.csv"
MODULE_FILENAME = "module.sv"
TESTBENCH_FILENAME = "testbench.sv"

class SetupNewTest(unittest.TestCase): 
    def is_test_name_invalid(self): 
        if (self.NEW_TEST_NAME == ""): return True
        self.assertEqual(type(self.NEW_TEST_NAME), str)

    def setup_dir(self): 
        if (self.is_test_name_invalid()): return

        os.makedirs(self.FULL_PATH)
        generator_path = os.path.join(self.FULL_PATH, PYTHON_GENERATOR_FILENAME)
        with open(generator_path, mode="x") as generator: 
            generator.write(
                """
def generator(a, b, c, d) -> tuple[int, int, int, int]:
    yield(a, b)
    yield(c, d)
"""
            )
            return f"\nSetup test at:\n{generator_path}"
    
    def running_python_generating_verilog(self): 
        if (self.is_test_name_invalid()): return ""
        return "\nPopulating Verilog"
    
    def test_setup(self): 
        self.NEW_TEST_NAME = "circle_lines" # MODIFY THIS
        self.DATA_PATH = f"data/{__name__}/test_{self.NEW_TEST_NAME}/"
        self.FULL_PATH = os.path.join(THIS_DIR, self.DATA_PATH)
        
        logs = "\n========== Test Setup =========="

        try: 
            logs += self.setup_dir()
            return
        except FileExistsError: 
            try: 
                logs += self.running_python_generating_verilog()
            except FileExistsError:    
                pass
            except: 
                self.fail("Unexpected Error")
        except: 
            self.fail("Unexpected Error")
        finally: 
            warnings.warn(logs + "\n========== Setup End ==========")

class TestGeneratorParser(unittest.TestCase): 
    def test_circle_lines(self): 
        TEST_CASE = [23, 17, 5, 0] # Args

        DATA_PATH = f"data/{__name__}/{inspect.currentframe().f_code.co_name}/"
        FULL_PATH = os.path.join(THIS_DIR, DATA_PATH)
        with open(os.path.join(FULL_PATH, PYTHON_GENERATOR_FILENAME)) as python_file:
            python = python_file.read() 
            _locals = dict()
            exec(python, None, _locals) # grab's exec's populated scoped variables

            tree = ast.parse(python)
            # warnings.warn(ast.dump(tree))
            generator_inst = _locals[NAMED_FUNCTION](*TEST_CASE)

            with open(os.path.join(FULL_PATH, EXPECTED_FILENAME), mode="w") as expected_file: 
                for tupl in generator_inst: 
                    expected_file.write(str(tupl)[1:-1] + "\n")
            
            with open(os.path.join(FULL_PATH, MODULE_FILENAME), mode="w") as module_file: 
                func = tree.body[0]
                genParser = GeneratorParser(func)
                module_file.write(str(genParser.generate_verilog()))

            warnings.warn(ast.dump(tree.body[0]))

            with open(os.path.join(FULL_PATH, TESTBENCH_FILENAME), mode="w") as testbench_file: 
                text = """module generator_tb;
  // Inputs
  reg _clock;
  reg _start;
""" # TODO: use the NAMED_FUNCTION constant instead of generator
                for i, v in enumerate(tree.body[0].args.args): 
                    text += f"  reg signed [31:0] {v.arg};\n"
                text += "\n  // Outputs\n"
                for i in range(len(tree.body[0].returns.slice.elts)): 
                    text += f"  wire signed [31:0] _out{i};\n"
                
                text += """
  wire _done;

  // Instantiate the module under test
  generator dut (
    ._clock(_clock),
    ._start(_start),
"""
                for i, v in enumerate(tree.body[0].args.args): 
                    text += f"    .{v.arg}({v.arg}),\n"
                for i in range(len(tree.body[0].returns.slice.elts)): 
                    text += f"    ._out{i}(_out{i}),\n"
                
                # TODO: auto-populate test case args data
                text += """
    ._done(_done)
  );

  // Clock generation
  always #5 _clock = !_clock;

  // Stimulus
  initial begin
    // Initialize inputs
    _start = 0;
    a = 23;
    b = 17;
    c = 5;
    d = 0;
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
      $display(\"""" # TODO: use NAMED_FUNCTION instead of "generator dut"
                
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
                    with open(os.path.join(FULL_PATH, EXPECTED_FILENAME)) as exp_f:
                        with open(os.path.join(FULL_PATH, ACTUAL_FILENAME)) as act_f:
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

                            self.assertEqual(actual_coords - expected_coords, set(), f"Extra coordinates: {str(actual_coords - expected_coords)} {str(actual_coords)} {str(expected_coords)}")
                            self.assertEqual(expected_coords - actual_coords, set(), f"Missing Coordinates: {str(expected_coords - actual_coords)} {str(actual_coords)} {str(expected_coords)}")

                            return "Running test"
                

