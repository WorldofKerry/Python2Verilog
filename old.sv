module my_func (
    // Function parameters (only need to be set when start is high):

    input wire _clock, // clock for sync
    input wire _reset, // set high to reset, i.e. done will be high
    input wire _start, // set high to capture inputs (in same cycle) and start generating

    // Implements a ready/valid handshake based on
    // http://www.cjdrake.com/readyvalid-protocol-primer.html
    input wire _ready, // set high when caller is ready for output
    output reg _valid, // is high if output values are valid

    output reg _done, // is high if module done outputting

    // Output values as a tuple with respective index(es)
    output reg signed [31:0] _out0
);
    // State variables
    typedef enum{_state0_assign0,_state1_assign0,_state2_assign0,_state3_while,_state3_while0_assign0,_state3_while1_assign0,_state3_while2,_state_done,_state_idle} _state_t;
    _state_t _state;
    // Global variables
    reg signed [31:0] _a;
    reg signed [31:0] _b;
    reg signed [31:0] _count;
    reg signed [31:0] _n;
    // Core
    always @(posedge _clock) begin
        `ifdef DEBUG
        $display("my_func,%s,_start=%0d,_done=%0d,_ready=%0d,_valid=%0d,_out0=%0d,_n=%0d,_a=%0d,_b=%0d,_count=%0d", _state.name, _start, _done, _ready, _valid, _out0, _n, _a, _b, _count);
        `endif
        _done <= 0;
        if (_ready) begin
            _valid <= 0;
        end
        // Start signal takes precedence over reset
        if (_reset) begin
            _state <= _state_idle;
        end
        if (_start) begin
            _n <= $signed(10);
            _state <= _state1_assign0;
        end else begin
            // If ready or not valid, then continue computation
            if ((_ready || !(_valid))) begin
                case (_state)
                    _state1_assign0: begin
                        _a <= $signed(0);
                        _b <= $signed(1);
                        _state <= _state2_assign0;
                    end
                    _state2_assign0: begin
                        _count <= $signed(1);
                        _state <= _state3_while;
                    end
                    _state3_while: begin
                        if ((_count < _n)) begin
                            _state <= _state3_while0_assign0;
                        end else begin
                            _state <= _state_done;
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
                    _state3_while0_assign0: begin
                        _out0 <= _a;
                        _valid <= 1;
                        _state <= _state3_while1_assign0;
                    end
                    _state3_while1_assign0: begin
                        _a <= _b;
                        _b <= $signed(_a + _b);
                        _state <= _state3_while2;
                    end
                    _state3_while2: begin
                        _count <= $signed(_count + $signed(1));
                        _state <= _state3_while;
                    end
                endcase
            end
        end
    end
endmodule

/*
MIT License

Copyright (c) 2023 Kerry Wang

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
*/
