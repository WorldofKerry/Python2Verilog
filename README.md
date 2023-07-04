# Python To Verilog

Converts a subset of python generator functions into synthesizable verilog.
A sample can be found in `tests/` under the files with prefix `rectangle_lines_*`, where the code outputs points on a grid that form the lines that make up a rectangle.

Based on my experimentation with a [C to Verilog converter](https://github.com/WorldofKerry/c2hdl)

## Live Docs

`python3 -m pydoc -b`

## TODO

- Change all `[Lines, Lines]` to `(Lines, Lines)` as tuples have fixed length for function hint
- Think about what should come at the end of statements handler, should it increment the state by default? should it reset to zero as default?, multiple TODOs in code for this
- not require different i names for range
- test verilog somehow? assert against python output
- auto-generate verilog testbench
- create python test interface using `for .. in`
  - various numerical patterns
- streamline python test framework, output `ast.dump`, python output and verilog output
