#!/bin/bash -e

python3 -m pydoc -w python2verilog
mv python2verilog.html docs/

python3 -m pydoc -w python2verilog.parsers
mv python2verilog.parsers.html docs/

python3 -m pydoc -w python2verilog.parsers.generator
mv python2verilog.parsers.generator.html docs/

python3 -m pydoc -w python2verilog.parsers.utils
mv python2verilog.parsers.utils.html docs/

echo "Documentation in docs/"
