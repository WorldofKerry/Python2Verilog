![Python Package](https://github.com/worldofkerry/python2verilog/actions/workflows/python-package.yml/badge.svg)
[![Documentation Status](https://readthedocs.org/projects/python2verilog/badge/?version=latest)](https://python2verilog.readthedocs.io/en/latest/?badge=latest)
![PyPI](https://img.shields.io/pypi/v/python2verilog?label=pypi%20package)
![PyPI - Downloads](https://img.shields.io/pypi/dm/python2verilog)

# Python 2 Verilog

Converts a subset of python generator functions into synthesizable sequential SystemVerilog.

A use case is for drawing shapes on grids (for VGA output), where the user may prototype the algorithm in python and then convert it to verilog for use in an FPGA.

A testbench can also be generated and asserted against the Python outputs.

Supports Python [Generator functions](https://wiki.python.org/moin/Generators) as well as the following block types:

- `if`
- `while`

**Warning**: Variables are treated as global and therefore no variable shadowing.

## Sample Usage
`pip install python2verilog`

### Basic Usage
Create a python file containing a generator function with output type hints, named `<name>.py`.

A sample can be found [here](https://github.com/WorldofKerry/Python2Verilog/blob/main/tests/integration/data/integration/circle_lines/python.py)

`python3 -m python2verilog.convert <name>.py`. Use `--help` for additional options, including outputting a testbench.

## Testing

### Requirements

Warning: may be outdated, refer to [github workflow](.github/workflows/python-package.yml) for most update-to-date information for Ubuntu.

Verilog simulation: `sudo apt-get install iverilog expected` (uses the `unbuffer` app in `expected`). The online simulator [EDA Playground](https://edaplayground.com/) can be used as a subsitute, given that you paste the output into the "actual file" specified in the `config.ini` of the test.

Python Libraries: `python3 -m pip install -r tests/requirements.txt`

### Creating New Test

To create a new test case and set up configs, run `python3 tests/integration/new_test_case.py <test-name>`.

### Running Tests

To run tests, use `python3 -m pytest --verbose` to generate the module, testbench, visualizations, dumps, and expected/actual outputs.
Those files will be stored in `tests/integration/data/integration/<test-name>/`.

## Tested Generations

Outputs of tests in repo can be found as a [github workflow artifact](https://nightly.link/WorldofKerry/Python2Verilog/workflows/python-package/main/tests-data.zip)

## For Developers

Based on my experimentation with a [C to Verilog converter](https://github.com/WorldofKerry/c2hdl).

Architecture is based on [LLVM](https://llvm.org/).

To setup pre-commit, run `pre-commit install`.

### Epics

- Support arrays
- Mimic combinational logic with "regular" Python functions
- Division approximations

## Docs

- cd to `docs/`
- `sphinx-apidoc -o . ../python2verilog/`
- `make html`

## Random Planning, Design, and Notes

## What needs to be duplicated in testbenches?
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
