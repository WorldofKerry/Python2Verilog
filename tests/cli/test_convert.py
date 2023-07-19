import subprocess
import warnings
import unittest


class TestConvert(unittest.TestCase):
    def test_help(self):
        result = subprocess.run(
            "python3 -m python2verilog.convert --help",
            shell=True,
            text=True,
            capture_output=True,
        )
        if result.returncode:
            warnings.warn(result.stdout + result.stderr)
            raise subprocess.CalledProcessError("non-zero return code")

    def test_conversion(self):
        result = subprocess.run(
            'python3 -m python2verilog.convert tests/integration/data/integration/happy_face/python.py \
                -o tests/cli/module.sv -t tests/cli/testbench.sv -c "[(4, 8, 3), (12, 17, 7)]"',
            shell=True,
            text=True,
            capture_output=True,
        )
        if result.returncode:
            warnings.warn(result.stdout + result.stderr)
            raise subprocess.CalledProcessError("non-zero return code")
