import subprocess
import warnings
import unittest


class TestConvert(unittest.TestCase):
    def test_help(self):
        CMD = "python3 -m python2verilog --help"
        result = subprocess.run(
            CMD,
            shell=True,
            text=True,
            capture_output=True,
        )
        if result.returncode:
            warnings.warn(result.stdout + result.stderr)
            raise subprocess.CalledProcessError(CMD, "non-zero return code")

    def test_module(self):
        CMD = "python3 -m python2verilog tests/integration/data/happy_face/python.py \
                -o tests/cli/module.sv -O5"
        result = subprocess.run(
            CMD,
            shell=True,
            text=True,
            capture_output=True,
        )
        if result.returncode:
            warnings.warn(result.stdout + result.stderr)
            raise subprocess.CalledProcessError(CMD, "non-zero return code")

    def test_testbench(self):
        CMD = 'python3 -m python2verilog tests/integration/data/happy_face/python.py \
                -o tests/cli/module.sv -t tests/cli/testbench.sv -c "[(4, 8, 3), (12, 17, 7)]"'
        result = subprocess.run(
            CMD,
            shell=True,
            text=True,
            capture_output=True,
        )
        if result.returncode:
            warnings.warn(result.stdout + result.stderr)
            raise subprocess.CalledProcessError(CMD, "non-zero return code")

    def test_error(self):
        CMD = "python3 -m python2verilog tests/integration/data/happy_face/python.py \
                -o tests/cli/module.sv -t tests/cli/testbench.sv"

        def tb_path_no_case():
            result = subprocess.run(
                CMD,
                shell=True,
                text=True,
                capture_output=True,
            )
            if result.returncode:
                raise subprocess.CalledProcessError(
                    cmd=CMD, returncode=result.returncode, stderr="non-zero return code"
                )

        self.assertRaises(subprocess.CalledProcessError, tb_path_no_case)
