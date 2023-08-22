# Examples

Two ways of using this library

## Importing the Package (Recommended)

### Basic

`python3 decorator_basic.py`

### Advanced

`python3 -m pip install -r requirements.txt`

`python3 decorator_advanced.py`

## Command Line Interface

`python3 -m python2verilog cli.py -n happy_face -O1`

`python3 -m python2verilog cli.py -n happy_face -c "[(4, 8, 3), (12, 17, 7)]" -O1`

`python3 -m python2verilog cli.py -n happy_face -o module.sv -t testbench.sv -c "[(4, 8, 3), (12, 17, 7)]" -O1`
