import subprocess
import warnings
import unittest


class TestConvert(unittest.TestCase):
    def test_help(self):
        result = subprocess.run(
            "python3 -m python2verilog.convert --help",
            shell=True,
            text=True,
            check=True,
            capture_output=True,
        )
        # warnings.warn(result.stdout + result.stderr)

    def test_conversion(self):
        result = subprocess.run(
            "python3 -m python2verilog.convert tests/integration/data/integration/happy_face/python.py -o tests/cli/module.log",
            shell=True,
            text=True,
            check=True,
            capture_output=True,
        )
        # warnings.warn(result.stdout + result.stderr)
