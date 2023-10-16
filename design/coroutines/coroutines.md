# Coroutines

## Abstract

Many higher level langauges use coroutines as the basis of generator implementations. In particular, the state of the coroutine and the logic associated with it can often be seperated. For example, in C++20 coroutines, the "promise" contains the logic, and the interal state is kept seperately. This allows resuse of the promise, for multiple generator instances.

In the generator function spec of python2verilog, every named generator instance is converted to a Verilog module. This causes a lot of duplicate hardware, as the state logic (the same for every generator instance) is duplicated every time a new named instance is created. Here we will discuss how these two things can be seperated, and its affect on parallelism and performance.

## A Basic Example

Consider generator for a range of whole numbers less than `n`.

This can be written as

```python
def basic_range(n):
    counter = 0
    while counter < n:
        yield counter
        counter += 1
```

When transpiled, we get

```verilog
        if (_start) begin
            _n <= n;
            _counter <= $signed(0);
            if (($signed(0) < n)) begin
                _out0 <= $signed(0);
                _valid <= 1;
                _counter <= $signed($signed(0) + $signed(1));
                _state <= _state1_while;
            end else begin
                if ((!(_valid) && _ready)) begin
                    _done <= 1;
                    _state <= _state_idle;
                end else begin
                    _state <= _state_done;
                end
            end
        end else begin
            // If ready or not valid, then continue computation
            if ((_ready || !(_valid))) begin
                case (_state)
                    _state1_while: begin
                        if ((_counter < _n)) begin
                            _out0 <= _counter;
                            _valid <= 1;
                            _counter <= $signed(_counter + $signed(1));
                            if (($signed(_counter + $signed(1)) < _n)) begin
                                _state <= _state1_while0_assign0;
                            end else begin
                                if ((!(_valid) && _ready)) begin
                                    _done <= 1;
                                    _state <= _state_idle;
                                end else begin
                                    _state <= _state_done;
                                end
                            end
                        end else begin
                            if ((!(_valid) && _ready)) begin
                                _done <= 1;
                                _state <= _state_idle;
                            end else begin
                                _state <= _state_done;
                            end
                        end
                    end
                    _state1_while0_assign0: begin
                        _out0 <= _counter;
                        _valid <= 1;
                        _counter <= $signed(_counter + $signed(1));
                        if (($signed(_counter + $signed(1)) < _n)) begin
                            _state <= _state1_while0_assign0;
                        end else begin
                            if ((!(_valid) && _ready)) begin
                                _done <= 1;
                                _state <= _state_idle;
                            end else begin
                                _state <= _state_done;
                            end
                        end
                    end
                    _state_done: begin
                        if ((!(_valid) && _ready)) begin
                            _done <= 1;
                            _state <= _state_idle;
                        end else begin
                            _state <= _state_done;
                        end
                    end
                endcase
            end
        end
```
