from pycde import Input, Module, Output, System, fsm, generator
from pycde.common import Clock, Reset
from pycde.dialects import comb
from pycde.testing import unittestmodule
from pycde.types import types


class F0(fsm.Machine):
    a = Input(types.i1)
    b = Input(types.i1)
    c = Input(types.i1)

    def maj3(ports):
        def nand(*args):
            return comb.XorOp(comb.AndOp(*args), types.i1(1))

        c1 = nand(ports.a, ports.b)
        c2 = nand(ports.b, ports.c)
        c3 = nand(ports.a, ports.c)
        return nand(c1, c2, c3)

    idle = fsm.State(initial=True)
    (A, B, C) = fsm.States(3)

    idle.set_transitions((A,))
    A.set_transitions((B, lambda ports: ports.a))
    B.set_transitions((C, maj3))
    C.set_transitions(
        (idle, lambda ports: ports.c),
        (A, lambda ports: comb.XorOp(ports.b, types.i1(1))),
    )


system = System([F0], output_directory="exsys", name="bruvlmao")
system.compile()
