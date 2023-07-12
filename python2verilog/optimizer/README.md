# Optimizer

Responsible for optimizing Verilog AST.

## Optimization Ideas
Should take inspiration from LLVM.

- Making use of Verilog for loops for duplication of hardware.
- Combining series of assign statements into a single assign (by expanding nonblocking assignments via if / tertiary), basic logic in [C to Verilog converter](https://github.com/WorldofKerry/c2hdl).
- Unrolling of loops, and balancing operations that can be parallelized [source](https://llvm.org/devmtg/2010-11/Rotem-CToVerilog.pdf).
