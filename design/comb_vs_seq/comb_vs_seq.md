# Combinational vs Sequential FSM

Take a Python generator snippet

```python
# pre
if a:
    if b:
        yield c
    yield d # other
else:
    yield b
# post
```

To translate into Verilog, there are two ways

## Combinational Basis

```verilog
always_ff state <= next_state;
always_comb case
    pre: begin
        if (a) begin
            if (b) begin
                out = c;
                next_state = pre;
            else begin
                out = d;
                next_state = done;
            end
        else begin
            out = b;
            next_state = done;
        end
    end
    other: begin
        out = d;
        next_state = done;
    end
    done: begin
        ...
    end
endcase
```

## Sequential Basis

```verilog
always_ff case
    pre: begin
        if (a) begin
            if (b) begin
                out <= c;
                state <= pre;
            else begin
                out <= d;
                state <= done;
            end
        else begin
            out <= b;
            state <= done;
        end
    end
    other: begin
        out <= d;
        state <= done;
    end
    done: begin
        ...
    end
endcase
```

## Conclusion

The sequential basis causes the output to take one cycle longer to appear.

However, is this cycle overhead only there at the very start and end of the FSM?
