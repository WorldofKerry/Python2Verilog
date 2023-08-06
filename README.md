[![pypi](https://img.shields.io/pypi/v/python2verilog?label=pypi%20package)](https://pypi.org/project/python2verilog/)
![py versions](https://img.shields.io/badge/dynamic/yaml?url=https%3A%2F%2Fraw.githubusercontent.com%2FWorldofKerry%2FPython2Verilog%2Fmain%2F.github%2Fworkflows%2Fpytest.yml&query=%24.jobs.build.strategy.matrix%5B%22python-version%22%5D&label=python%20versions)
[![pypi downloads](https://img.shields.io/pypi/dm/python2verilog)](https://pypi.org/project/python2verilog/)
[![pytest](https://github.com/worldofkerry/python2verilog/actions/workflows/pytest.yml/badge.svg)](https://github.com/WorldofKerry/Python2Verilog/actions/workflows/pytest.yml)
[![docs](https://github.com/worldofkerry/python2verilog/actions/workflows/sphinx.yml/badge.svg)](https://worldofkerry.github.io/Python2Verilog/)

# python2verilog

Converts a subset of python generator functions into synthesizable sequential SystemVerilog.

A use case is for drawing shapes on grids (for VGA output), where the user may prototype the algorithm in python and then convert it to verilog for use in an FPGA.

Supports Python [Generator functions](https://wiki.python.org/moin/Generators) as well as the following block types:

- `if`
- `while`
  A testbench can also be generated and asserted against the Python outputs.

## Usage

## Download Package

`python3 -m pip install --upgrade pip`  
`python3 -m pip install python2verilog`

### Run Basic Converter

Create a python file containing a generator function with output type hints, named `python.py`.

If you want a sample, get one with `wget https://github.com/worldofkerry/python2verilog/raw/main/tests/integration/data/circle_lines/python.py`. More samples can be found [here](https://github.com/WorldofKerry/Python2Verilog/blob/main/tests/integration/data/).

Run `python3 -m python2verilog python.py` to write a Verilog module to `python.sv`. Use `--help` to see additional options, including outputting a testbench and using optimizations.

## Testing

### Requirements

Ubuntu (no WSL). Refer to [pytest workflow](.github/workflows/pytest.yml) for most update-to-date information.

Verilog simulation: `sudo apt-get install iverilog expected` (uses the `unbuffer` app in `expected`). Alternatively [EDA Playground](https://edaplayground.com/) can be used as a subsitute, by copy-pasting the module and testbench files to the simulator.

Python Libraries: `python3 -m pip install -r tests/requirements.txt`

### Creating New Test

To create a new test case and set up configs, run `python3 tests/integration/new_test_case.py <test-name>`.

### Running Tests

To run tests, use `python3 -m pytest --verbose` to generate the module, testbench, visualizations, dumps, and expected/actual outputs.
Those files will be stored in `tests/integration/data/integration/<test-name>/`.

## Tested Generations

The Github Actions run all the tests with writing enabled.
You may find its output as a [Github Artifact](https://nightly.link/WorldofKerry/Python2Verilog/workflows/pytest/main/tests-data.zip).

## For Developers

To setup pre-commit, run `pre-commit install`.

[Github Issues](https://github.com/WorldofKerry/Python2Verilog/issues) is used for tracking.

### Epics

- Support arrays (and their unrolling)
- Mimic combinational logic with "regular" Python functions
- Division approximations (and area/timing analysis)

## Docs

Uses sphinx.
Run commands used by [Github Actions](.github/workflows/sphinx.yml).

## Random Planning, Design, and Notes

### What needs to be duplicated in testbenches?

declare I/O and other signals
declare DUT
start clock

loop for each test case

- start signal
- while wait for done signal
  - clock
  - set start zero
  - display output
    endloop

### Potential API

```python
import python2verilog as p2v
import ast

func = ast.parse(code).body[0]

ir = p2v.from_python_get_ir(func.body)

# Optimization passes
ir = p2v.optimizations.replace_single_item_cases(ir)
ir = p2v.optimizations.remove_nesting(ir)
ir = p2v.optimizations.combine_statements(ir)

verilog = p2v.Verilog()
verilog.from_python_do_setup(ir.get_context()) # module I/O is dependent on Python
verilog.from_ir_fill_body(ir.get_root()) # fills the body

# whether has valid or done signal,
# whether initialization is always happening or only on start,
# verilog sim name
verilog.config(has_valid=True, has_done=True, lazy_start=True, verilog_sim="iverilog")

with open(f"{verilog.get_module_name()}.sv", mode="w") as module:
  module.write(verilog.get_module())
with open(f"{verilog.get_module_name()}_tb.sv", mode="w") as tb:
  tb.write(verilog.get_testbench())

print(verilog.get_verilog_run_cmd())
assert verilog.test_outputs() # checks if verilog and python output same
```

### Rectangle Filled

```python
def draw_rectangle(s_x, s_y, height, width) -> tuple[int, int]:
    for i0 in range(0, width):
        for i1 in range(0, height):
            yield (s_x + i1, s_y + i0)
```

```verilog
case (STATE)
  0: begin
    if (i0 < width) begin
      STATE <= STATE_1;
    end else begin
      case (STATE_INNER)
        0: begin
          if (i1 < height) begin
            STATE_INNER <= STATE_INNER + 1;
          end else begin
            case (STATE_INNER_INNER)
              0: begin
                out0 <= s_x + i1;
                out1 <= s_y + i0;
                i1 <= i1 + 1;

                STATE_INNER_INNER <= STATE_INNER_INNER + 1;
                STATE_INNER_INNER <= 0; // flag to either wrap around or remain
              end
          end
          STATE_INNER <= 0;
        end
      endcase
    end
  end
  STATE_1: begin
    done <= 1;
  end
endcase
```

## Converting a While Loop

```python
i = 0
while <condition>:
    <statement 1>
    <statement 2>
    ...
```

```verilog
case (STATE)
  0: begin
    // For loop start
    if (condition) begin
      STATE <= STATE + 1;
    end else begin
      case (STATE_INNER)
        0: begin
          // statement 1
        end
        1: begin
          // statement 2
        end
        // ...
        10: begin
          STATE_INNER <= 0;
        end
      endcase
    end
    // For loop end
  end
  // ...
endcase
```

## If Statement Analysis

```verilog
// IF START
case (_STATE_IF)
  0: begin
    if (condition) _STATE_IF <= 1;
    else _STATE_IF <= 2;
  end
  1: begin
    // THEN BODY START
    case ()
    // ...
      _STATE_IF <= 0;
    // THEN BODY END
  end
  2: begin
    // ELSE BODY START
    // ...
     __STATE_IF <= 0;
    // ELSE BODY END
  end
endcase
// IF END
```
