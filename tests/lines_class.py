from setup import python2verilog as p2v, output

list_buffers = [
    [p2v.Lines(["a0", "b0"]), p2v.Lines(["c0", "d0"])],
    [p2v.Lines(["a1", "b1"]), p2v.Lines(["c1", "d1"])],
    [p2v.Lines(["a2", "b2"]), p2v.Lines(["c2", "d2"])],
]


lines1 = p2v.Lines.nestify(list_buffers)
with output(__file__) as f: 
    for i, v in enumerate(lines1):
        f.write(f"{i}\n")
        f.write(f"{v}\n")
