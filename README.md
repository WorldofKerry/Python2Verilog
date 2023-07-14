# Python 2 Verilog

Converts a subset of python generator functions into synthesizable sequential SystemVerilog.

A use case is for drawing shapes on grids (for VGA output), where the user may prototype the algorithm in python and then convert it to verilog for use in an FPGA.

A testbench is also generated and asserted against the Python outputs.

Supports Python [Generator functions](https://wiki.python.org/moin/Generators) as well as the following block types:

- `if`
- `while`
- `for ... in range(...)` with 1 or 2 args in `range` (quite inefficient)

**Warning**: Variables must be unique, i.e. variables do not have block scope, e.g. the following modifies global `i`:

```python
for i in range(10):
    pass
```
## Sample Usage
`pip install python2verilog==0.0.1`

```python
from python2verilog.frontend.generator import GeneratorParser
import ast

func = """
def circle_lines(s_x, s_y, height) -> tuple[int, int]:
    x = 0
    y = height
    d = 3 - 2 * height
    yield (s_x + x, s_y + y)
    yield (s_x + x, s_y - y)
    yield (s_x - x, s_y + y)
    yield (s_x - x, s_y - y)
    yield (s_x + y, s_y + x)
    yield (s_x + y, s_y - x)
    yield (s_x - y, s_y + x)
    yield (s_x - y, s_y - x)
    while y >= x:
        x = x + 1
        if d > 0:
            y = y - 1
            d = d + 4 * (x - y) + 10
        else:
            d = d + 4 * x + 6
        yield (s_x + x, s_y + y)
        yield (s_x + x, s_y - y)
        yield (s_x - x, s_y + y)
        yield (s_x - x, s_y - y)
        yield (s_x + y, s_y + x)
        yield (s_x + y, s_y - x)
        yield (s_x - y, s_y + x)
        yield (s_x - y, s_y - x)
"""
generatorParser = GeneratorParser(ast.parse(func).body[0])
print(generatorParser.generate_verilog())
```

## Automatically Test The Generated Verilog
`python3 tests/parsers/new_generator.py <name>` to create new test case and prepare template Python file.

`python3 -m pytest --verbose` to run tests / generate the module, testbench, visualizations, dumps, and expected/actual outputs.

## Tested Generations
The outputs of the Python script tests can be found [here](https://nightly.link/WorldofKerry/Python2Verilog/workflows/python-package/main/data-generator.zip)

Python vs Verilog stats on sample inputs (not up-to-date) can be found [here](tests/frontend/data/generator/stats.md).

I recommend [EDA Playground](https://edaplayground.com/) or [Icarus Verilog](https://github.com/steveicarus/iverilog) for testing the verilog code. Refer to the [github action](.github/workflows/python-package.yml) to see how to setup testing with Icarus Verilog.

## For Developers
Based on my experimentation with a [C to Verilog converter](https://github.com/WorldofKerry/c2hdl).

Architecture is based on [LLVM](https://llvm.org/).

To setup pre-commit, run `pre-commit install`.

### Epics

- Create a Verilog AST representation (lots of samples online) to better optimize (mostly end statements)
- Add `valid` signal and then generate testbenches that test multiple cases

## Docs

- Generate `.html` docs: `bash docs/generate.sh`
- Live docs: `python3 -m pydoc -b`

## Random Planning, Design, and Notes

### Potential API
```python
import python2verilog as p2v
import ast

func = ast.parse(code).body[0]

ir = p2v.from_python_get_ir(func.body) # returns an ir node for the root of the body

# Optimization passes
ir = p2v.optimizations.replace_single_item_cases(ir)
ir = p2v.optimizations.remove_nesting(ir)
ir = p2v.optimizations.combine_statements(ir)
for i in dir(p2v.optimizations): # Do one pass of every optimization
  item = getattr(pv2.optimizations, i)
    if callable(item):
      ir = item(ir)

verilog = p2v.Verilog()
verilog.from_python_do_setup(func) # module I/O is dependent on Python
verilog.from_ir_fill_body(ir) # fills the body

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
