[![pypi](https://img.shields.io/pypi/v/python2verilog?label=pypi%20package)](https://pypi.org/project/python2verilog/)
![py versions](https://img.shields.io/badge/dynamic/yaml?url=https%3A%2F%2Fraw.githubusercontent.com%2FWorldofKerry%2FPython2Verilog%2Fmain%2F.github%2Fworkflows%2Fpytest.yml&query=%24.jobs.build.strategy.matrix%5B%22python-version%22%5D&label=python%20versions)
[![pypi downloads](https://img.shields.io/pypi/dm/python2verilog)](https://pypi.org/project/python2verilog/)
[![pytest](https://github.com/worldofkerry/python2verilog/actions/workflows/pytest.yml/badge.svg)](https://github.com/WorldofKerry/Python2Verilog/actions/workflows/pytest.yml)
[![docs](https://github.com/worldofkerry/python2verilog/actions/workflows/sphinx.yml/badge.svg)](https://worldofkerry.github.io/Python2Verilog/)

# python2verilog

Converts a subset of python functions into synthesizable sequential SystemVerilog.

A testbench can also be generated if the user provides testcases or uses the function in their Python code. 

The testbenchs' results can also asserted against the Python outputs (not included in package but as apart of this repo due to third-party simulation tools).

A use case is for drawing shapes on grids (for VGA output), where the user may prototype the algorithm in Python and then convert it to Verilog for use in an FPGA.

Constrains on Python functions include: 
- Supports only `if` and `while` blocks
- Supports only integral types and operations
- Must be a [generator function](https://wiki.python.org/moin/Generators)
- Must be a [pure function](https://en.wikipedia.org/wiki/Pure_function)

Unsupported Python paradigms include but are not limited to the following: 
- Regular functions that use the `return` keyword, instead `yield` once
- `for` loops, instead rewrite as a while loop
- Function calls, instead use the converter on each of the subfunctions

## Usage

For an online demo, checkout out this [Replit project](https://replit.com/@WorldofKerry/Python2Verilog-Demo)! No guarantees on the up-to-dateness of this demo.

### Installation

`python3 -m pip install --upgrade pip`

`python3 -m pip install python2verilog`

### Basics

Create a python file containing a generator function with output type hints, named `python.py`.

You can find a sample [here](https://github.com/WorldofKerry/Python2Verilog/blob/main/tests/integration/data/happy_face/python.py), and a directory of samples [here](https://github.com/WorldofKerry/Python2Verilog/tree/main/tests/integration/data)

Run `python3 -m python2verilog python.py` to generate a testbench file at `python.sv`.

Use the arg `--help` for additional options, including outputting a testbench and running optimizers.

## Tested Generations

The Github Actions run all the tests with writing enabled.
You may find its output as a [Github Artifact](https://nightly.link/WorldofKerry/Python2Verilog/workflows/pytest/main/tests-data.zip) availible for download.

## For Developers

To setup pre-commit, run `pre-commit install`.

[Github Issues](https://github.com/WorldofKerry/Python2Verilog/issues) is used for tracking. Milestones and labels are used for milestones and labels respectively 😉

### Docs

Sphinx is used. Follow what [Github workflow](.github/workflows/sphinx.yml) uses to generate local copy.

## Testing

### Requirements

For most up-to-date information, refer to the pytest [github workflow](.github/workflows/python-package.yml).

A Ubuntu environment (WSL2 works too, make sure to have the repo on the Ubuntu partition, as [`os.mkfifo`](https://docs.python.org/3/library/os.html#os.mkfifo) is used to avoid writing to disk)

Install required python libraries with `python3 -m pip install -r tests/requirements.txt`

For automatic Verilog simulation and testing, install [Icarus Verilog](https://github.com/steveicarus/iverilog) and its dependencies with
`sudo apt-get install iverilog expected` (uses the `unbuffer` in `expected`).

The online simulator [EDA Playground](https://edaplayground.com/) can be used as a subsitute if you manually copy-paste the module and testbench files to it.

### Creating New Test

To create a new test case and set up configs, run `python3 tests/integration/new_test_case.py <test-name>`.

### Running Tests

To run tests, use `python3 -m pytest -sv`.

Additional CLI flags can be found in [tests/conftest.py](tests/conftest.py).

Use `git clean -dxf` to remove gitignored and generated files.
