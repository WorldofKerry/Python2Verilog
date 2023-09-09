# Function Calls

```python
@verilogify(write=True, overwrite=True, optimization_level=1)
def hrange(base, limit, step):
    i = base
    while i < limit:
        yield i
        i += step


@verilogify(write=True, overwrite=True, optimization_level=1)
def dup_range(base, limit, step):
    inst = hrange(base, limit, step) # 1
    for value in inst: # 2
        yield value # 3
        yield value + 1 # 4
```

```cpp
// ...
hrange _inst(
    .base(_hrange_inst_base),
    .limit(_hrange_inst_limit),
    .step(_hrange_inst_step),
    ._0(_hrange_inst__0),
    ._ready(_hrange_inst__ready),
    // ...
)
// ...
case (_state) begin
    _state_1: begin
        _hrange_inst_base <= _base;
        _hrange_inst_limit <= _limit;
        _hrange_inst_base <= _step;
        _hrange_inst__start <= 1;
        _hrange_inst__ready <= 0; // optimizer pass can set this to 1
        _state <= _state_2;
    end
    _state_2: begin
        _hrange_inst__ready <= 1;
        if (_hrange_inst__ready && _hrange_inst__valid) begin
            _value <= _hrange_inst__0;
            _state <= _state_3;
            _hrange_inst__ready <= 0;
        end
        if (_hrange_inst__done) begin
            _state <= _state_done;
            _hrange_inst__ready <= 0;
        end
    end
    _state_3: begin
        valid <= 1;
        _0 <= value;
        _state <= _state_4;
    end
    _state_4: begin
        valid <= 1;
        _0 <= value + 1;
        _state <= _state_2;
    end
    _state_done: // ...
end
// ...
```
