import logging
import subprocess
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
            logging.error(result.stdout + result.stderr)
            raise subprocess.CalledProcessError(CMD, "non-zero return code")

    # def test_module(self):
    #     CMD = "python3 -m python2verilog tests/integration/data/happy_face/python.py \
    #             -o tests/api/module.sv -O5 --name happy_face"
    #     result = subprocess.run(
    #         CMD,
    #         shell=True,
    #         text=True,
    #         capture_output=True,
    #     )
    #     if result.returncode:
    #         logging.error(result.stdout + result.stderr)
    #         raise subprocess.CalledProcessError(CMD, "non-zero return code")

    def test_testbench(self):
        CMD = 'python3 -m python2verilog tests/integration/data/happy_face/python.py -n happy_face \
                -o tests/api/module.sv -t tests/api/testbench.sv -c "[(4, 8, 3), (12, 17, 7)]"'
        result = subprocess.run(
            CMD,
            shell=True,
            text=True,
            capture_output=True,
        )
        if result.returncode:
            logging.error(result.stdout + result.stderr)
            raise subprocess.CalledProcessError(CMD, "non-zero return code")

    def test_err(self):
        CMD = "python3 -m python2verilog tests/integration/data/happy_face/python.py -n happy_face \
                -o tests/api/module.sv -t tests/api/testbench.sv"

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
