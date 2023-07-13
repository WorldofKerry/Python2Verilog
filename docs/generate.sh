#!/bin/bash -e

python3 -m pydoc -w python2verilog
mv python2verilog.html docs/

python3 -m pydoc -w python2verilog.frontend
mv python2verilog.frontend.html docs/

python3 -m pydoc -w python2verilog.frontend.generator
mv python2verilog.frontend.generator.html docs/

python3 -m pydoc -w python2verilog.frontend.utils
mv python2verilog.frontend.utils.html docs/

echo "Documentation in docs/"
