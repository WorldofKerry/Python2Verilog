import logging

logging.root.setLevel(logging.DEBUG)

from python2verilog.api import convert_file_to_file


def fib(n):
    yield (n)


fib(10)

convert_file_to_file("fib", __file__)
