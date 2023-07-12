#!/bin/bash
parent_path=$( cd "$(dirname "${BASH_SOURCE[0]}")" ; pwd -P )
cd "$parent_path"


iverilog -s generator_tb data/generator/delete_me/module.sv data/generator/delete_me/testbench.sv && unbuffer vvp a.out > data/generator/delete_me/actual.csv && cat data/generator/delete_me/actual.csv
iverilog -s generator_tb data/generator/rectangle_lines/module.sv data/generator/rectangle_lines/testbench.sv && unbuffer vvp a.out > data/generator/rectangle_lines/actual.csv && cat data/generator/rectangle_lines/actual.csv
iverilog -s generator_tb data/generator/rectangle_filled/module.sv data/generator/rectangle_filled/testbench.sv && unbuffer vvp a.out > data/generator/rectangle_filled/actual.csv && cat data/generator/rectangle_filled/actual.csv
iverilog -s generator_tb data/generator/circle_lines/module.sv data/generator/circle_lines/testbench.sv && unbuffer vvp a.out > data/generator/circle_lines/actual.csv && cat data/generator/circle_lines/actual.csv
