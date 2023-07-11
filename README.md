# Python To Verilog

Converts a subset of python generator functions into synthesizable sequential SystemVerilog.

A use case is for drawing shapes on grids (for VGA output), where the user may prototype the algorithm in python and then convert it to verilog for use in an FPGA.

Based on my experimentation with a [C to Verilog converter](https://github.com/WorldofKerry/c2hdl)

Supported functions:

- `if`
- `while` (less robust)
- `for ... in range(...)` with 1 or 2 args in `range` (less robust)

**Warning**: Variables must be unique, i.e. variables do not have block scope, e.g. the following modifies global `i`:

```python
for i in range(10):
    pass
```

## Tested Generations

I recommend [EDA Playground](https://edaplayground.com/) for testing the verilog code.

`python3 -m pytest --verbose` to run tests / regenerate most of the files [here](tests/parsers/data/generator/)

`python3 tests/parsers/new_generator.py <name>` to create new test case and prepare template Python file.

To test verilog locally, an example command with Icarus Verilog is
`iverilog '-Wall' design.sv testbench.sv  && unbuffer vvp a.out`

Comparisons between Python and Verilog for sample inputs:
| Algorithm          | Python Yield Count | Verilog Clock ycles | Notes   |
| ------------------ | ------------------ | ------------------- | ------- |
| Rectangle Filled   | 35                 | 75                  | Working |
| Rectangle Lines    | 24                 | 37                  | Working |
| Bresenham's Circle | 40                 | 51                  | Working |

## Docs

- Generate `.html` docs: `docs/generate.sh`
- Live docs: `python3 -m pydoc -b`

## Random Planning, Design, and Notes

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
