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

- Support fixed-length arrays (potentially using Verilog for loops for parallelism)
- Create a Verilog AST representation (lots of samples online) to better optimize (mostly end statements)

## Docs

- Generate `.html` docs: `bash docs/generate.sh`
- Live docs: `python3 -m pydoc -b`

## Optimizer

### Thought Experiment

Lets look at two Python functions and how they **could** be transpiled to Verilog.

```python
def doubler(i, x, n):
    while (i < n)
        x = 2 * x
        i += 1
    yield(x)
```

```verilog
...
case (STATE): 
  0: begin
    if (i < n) begin
      x <= 2 * x;
      i <= i + 1;
    end else begin
      _out <= x;
      _valid <= 1;
      STATE <= 1;
    end
  end
...
```

The Python yields `O(1)` times, but the Verilog takes `O(n-i)` clock cycles. Is there a better way to optimize this without losing generality?

Lets look at another example.

```python
def matrix_iter(i, j, w, h): 
    while (i < w):
        while (j < h):
            yield (i, j)
            j += 1
        i += 1
        j = 0
```

```verilog
...
case (STATE): 
  0: 
    if (i < w) begin
      STATE <= 1;
    end else begin
      if (j < h) begin
        _out <= {i, j};
        _valid <= 1;
        j <= j + 1;
      end else begin
        _out <= {i + 1, 0};
        _valid <= 1;
        i <= i + 1;
        j <= 1;
      end
    end
```

Here the Python yields `O(hw - hi)` times, and the Verilog is able to match in number of clock cycles.

How does the optimizer distinguish between these two cases? Is the sole difference that one has yields in a loop and the other does not?
