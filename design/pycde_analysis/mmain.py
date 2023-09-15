from pycde import Input, Module, Output, System, generator
from pycde.types import Bits


class OrInts(Module):
    a = Input(Bits(32))
    b = Input(Bits(32))
    c = Output(Bits(32))

    @generator
    def construct(self):
        self.c = self.a | self.b


system = System([OrInts], name="ExampleSystem", output_directory="exsys")
system.compile()

print(system.print())
