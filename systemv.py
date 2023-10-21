from pycde import Input, Module, Output, System, generator
from pycde.behavioral import Else, EndIf, If
from pycde.dialects import sv
from pycde.types import Bits, SInt, UInt, types


class MyModule(Module):
    myif = sv.IfOp(123)


system = System([MyModule], output_directory="exsys", name="lmaooo")
system.compile
