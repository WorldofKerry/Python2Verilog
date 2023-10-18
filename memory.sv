module get_data (
    // Function parameters (only need to be set when start is high):
    input wire signed [31:0] addr,

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
    localparam _state0 = 0;
    localparam _state_done = 1;
    localparam _state_idle = 2;
    reg [31:0] _state;
    // Global variables
    reg signed [31:0] _addr;
    // Core
    always @(posedge _clock) begin
        `ifdef DEBUG
        $display("get_data,%s,_start=%0d,_done=%0d,_ready=%0d,_valid=%0d,addr=%0d,_addr=%0d,_out0=%0d", _state.name, _start, _done, _ready, _valid, addr, _addr, _out0);
        `endif
        if (_ready) begin
            _valid <= 0;
            _done <= 0;
        end
        // Start signal takes precedence over reset
        if ((_reset || _start)) begin
            _state <= _state_idle;
            _done <= 0;
            _valid <= 0;
        end
        if (_start) begin
            _addr <= addr;
            _state <= _state;
            _state <= _state;
            _out0 <= $signed(addr + $signed(420));
            _valid <= 1;
            _done <= 1;
        end else begin
            // If ready or not valid, then continue computation
            if ((_ready || !(_valid))) begin
                // case(_state)
                //Empty case block
                // endcase
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

module read32to8 (
    // Function parameters (only need to be set when start is high):
    input wire signed [31:0] base,
    input wire signed [31:0] count,

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
    localparam _state0 = 0;
    localparam _state2_while = 1;
    localparam _state2_while2_while = 2;
    localparam _state2_while2_while0_assign0 = 3;
    localparam _state_done = 4;
    localparam _state_done_assign0 = 5;
    localparam _state_idle = 6;
    reg [31:0] _state;
    // Global variables
    reg signed [31:0] _i;
    reg signed [31:0] _j;
    reg signed [31:0] _base;
    reg signed [31:0] _count;
    // ================ Function Instance ================
    reg [31:0] _data_get_data_addr;
    wire [31:0] _data_get_data_out0;
    wire _data_get_data__valid;
    wire _data_get_data__done;
    reg _data_get_data__start;
    reg _data_get_data__ready;
    get_data _data (
        .addr(_data_get_data_addr),
        ._out0(_data_get_data_out0),
        ._valid(_data_get_data__valid),
        ._done(_data_get_data__done),
        ._clock(_clock),
        ._start(_data_get_data__start),
        ._reset(_reset),
        ._ready(_data_get_data__ready)
        );
    // Core
    always @(posedge _clock) begin
        `ifdef DEBUG
        $display("read32to8,%s,_start=%0d,_done=%0d,_ready=%0d,_valid=%0d,base=%0d,count=%0d,_base=%0d,_count=%0d,_out0=%0d,_i=%0d,_j=%0d", _state.name, _start, _done, _ready, _valid, base, count, _base, _count, _out0, _i, _j);
        `endif
        _data_get_data__ready <= 0;
        _data_get_data__start <= 0;
        if (_ready) begin
            _valid <= 0;
            _done <= 0;
        end
        // Start signal takes precedence over reset
        if ((_reset || _start)) begin
            _state <= _state_idle;
            _done <= 0;
            _valid <= 0;
        end
        if (_start) begin
            _base <= base;
            _count <= count;
            _state <= _state;
            _i <= $signed(0);
            if (($signed(0) < count)) begin
                _data_get_data__ready <= 0;
                _data_get_data__start <= 1;
                _data_get_data_addr <= $signed(base + $signed(count * $signed(4)));
                _j <= $signed(0);
                if (($signed(0) < $signed(4))) begin
                    _out0 <= _data;
                    _valid <= 1;
                    _state <= _state2_while2_while;
                end else begin
                    _state <= _state2_while;
                end
            end else begin
                _done <= 1;
                _valid <= 1;
                _state <= _state_idle;
            end
        end else begin
            // If ready or not valid, then continue computation
            if ((_ready || !(_valid))) begin
                case (_state)
                    _state2_while: begin
                        if ((_i < _count)) begin
                            _data_get_data__ready <= 0;
                            _data_get_data__start <= 1;
                            _data_get_data_addr <= $signed(_base + $signed(_count * $signed(4)));
                            _j <= $signed(0);
                            _state <= _state2_while2_while;
                        end else begin
                            _done <= 1;
                            _valid <= 1;
                            _state <= _state_idle;
                        end
                    end
                    _state2_while2_while: begin
                        if ((_j < $signed(4))) begin
                            _out0 <= _data;
                            _valid <= 1;
                            if ((_j < $signed(4))) begin
                                _state <= _state2_while2_while0_assign0;
                            end else begin
                                if ((_i < _count)) begin
                                    _data_get_data__ready <= 0;
                                    _data_get_data__start <= 1;
                                    _data_get_data_addr <= $signed(_base + $signed(_count * $signed(4)));
                                    _j <= $signed(0);
                                    _state <= _state2_while2_while;
                                end else begin
                                    _state <= _state_done_assign0;
                                end
                            end
                        end else begin
                            if ((_i < _count)) begin
                                _data_get_data__ready <= 0;
                                _data_get_data__start <= 1;
                                _data_get_data_addr <= $signed(_base + $signed(_count * $signed(4)));
                                _j <= $signed(0);
                                _state <= _state2_while2_while;
                            end else begin
                                _done <= 1;
                                _valid <= 1;
                                _state <= _state_idle;
                            end
                        end
                    end
                    _state2_while2_while0_assign0: begin
                        _out0 <= _data;
                        _valid <= 1;
                        if ((_j < $signed(4))) begin
                            _state <= _state2_while2_while0_assign0;
                        end else begin
                            if ((_i < _count)) begin
                                _data_get_data__ready <= 0;
                                _data_get_data__start <= 1;
                                _data_get_data_addr <= $signed(_base + $signed(_count * $signed(4)));
                                _j <= $signed(0);
                                _state <= _state2_while2_while;
                            end else begin
                                _state <= _state_done_assign0;
                            end
                        end
                    end
                    _state_done_assign0: begin
                        _done <= 1;
                        _valid <= 1;
                        _state <= _state_idle;
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
