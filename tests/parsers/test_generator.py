from python2verilog.parsers import GeneratorParser
import unittest
import os
import inspect
import warnings

THIS_DIR = os.path.dirname(os.path.abspath(__file__))

class SetupNewTest(unittest.TestCase): 
    NEW_TEST_NAME = "rectangle_filled"
    DATA_PATH = f"data/{__name__}/test_{NEW_TEST_NAME}/"
    FULL_PATH = os.path.join(THIS_DIR, DATA_PATH)

    def is_test_name_invalid(self): 
        if (self.NEW_TEST_NAME == ""): return True
        self.assertEqual(type(self.NEW_TEST_NAME), str)

    def setup_dir(self): # change prefix
        if (self.is_test_name_invalid()): return

        os.makedirs(self.FULL_PATH)
        with open(os.path.join(self.FULL_PATH, "function.py"), mode="x"): 
            pass
    
    def populate_verilog(self): 
        if (self.is_test_name_invalid()): return
    
    def test_setup(self): 
        warnings.warn("Setup New Test")
        try: 
            self.setup_dir()
            warnings.warn("Setup test dirs")
            return
        except FileExistsError: 
            self.populate_verilog()
            warnings.warn("Generating verilog files")
        except: 
            self.fail("Unexpected Error")

class TestGeneratorParser(unittest.TestCase): 
    def test_circle_lines(self): 
        DATA_PATH = f"data/{__name__}/{inspect.currentframe().f_code.co_name}/"
        FULL_PATH = os.path.join(THIS_DIR, DATA_PATH)
        with open(os.path.join(FULL_PATH, "function.py")) as python: 
            pass
