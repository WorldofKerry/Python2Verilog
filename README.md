# Python To Verilog

Converts a subset of python generator functions into synthesizable verilog.
A sample can be found in `tests/` under the files with prefix `rectangle_lines_*`, where the code outputs points on a grid that form the lines that make up a rectangle.

Based on my experimentation with a [C to Verilog converter](https://github.com/WorldofKerry/c2hdl)

## Working Tests

I recommend [EDA Playground](https://edaplayground.com/) for testing the verilog code.

`python3 tests/rectangle_filled.py`

`python3 tests/rectangle_lines.py`

`python tests/circle_lines.py`

| Algorithm | Python Cycles | Verilog Cycles |
| --------- | ------------- | -------------- |
| Rectangle Filled | 12 | 34 |
| Rectangle Lines | 14 | 24 |
| Bresenham's Circle | 32 | 34 |

## Docs

Live docs: `python3 -m pydoc -b`

Docs `.html`: `python3 -m pydoc -w python2verilog`

## Backlog Tasks

### Features

- Think about what should come at the end of statements handler, should it increment the state by default? should it reset to zero as default?, multiple TODOs in code for this
- not require different i names for range
- localparam variables
- add `valid` flag to output (for when output is not always valid)
- Reduce cycles in some areas (convert if statements to cases for more consistent endStatements attachment?)

### Coding Excellence

- Change all `[Lines, Lines]` to `(Lines, Lines)` as tuples have fixed length for function hint
- Add consts for string literals (e.g. "_start")

### Test Framework

- Write script that generates all files for new test case
- auto-generate verilog testbench or create a generalized testbench (e.g. for 10 outputs)
- Stop adding to set once `done` becomes 1
- consider switching to pytest

## Planning

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