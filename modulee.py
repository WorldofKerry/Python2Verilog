from pycde import Input, Module, Output, System, generator
from pycde.behavioral import Else, EndIf, If
from pycde.types import Bits, SInt, UInt, types


class IfNested(Module):
    a = Input(types.i32)
    b = Input(types.i32)
    cond = Input(types.i1)

    out0 = Output(types.i32)

    @generator
    def build(ports):
        x = ports.a
        with If(ports.cond):
            x = Bits(32)(6)
            with If((ports.a.as_sint() > SInt(32)(3)).as_bits()):
                x = Bits(32)(2)
            EndIf()
        EndIf()
        ports.out0 = x


system = System([IfNested], output_directory="exsys", name="amodule")
system.compile()
