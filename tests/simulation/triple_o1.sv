/*

# Python Function
        @verilogify(namespace=goal_namespace, mode=Modes.OVERWRITE)
        def circle_lines(s_x, s_y, height) -> tuple[int, int, int, int, int, int]:
            x = 0
            y = height
            d = 3 - 2 * y
            yield (s_x + x, s_y + y, height, x, y, d)
            yield (s_x + x, s_y - y, height, x, y, d)
            yield (s_x - x, s_y + y, height, x, y, d)
            yield (s_x - x, s_y - y, height, x, y, d)
            yield (s_x + y, s_y + x, height, x, y, d)
            yield (s_x + y, s_y - x, height, x, y, d)
            yield (s_x - y, s_y + x, height, x, y, d)
            yield (s_x - y, s_y - x, height, x, y, d)
            while y >= x:
                x = x + 1
                if d > 0:
                    y = y - 1
                    d = d + 4 * (x - y) + 10
                else:
                    d = d + 4 * x + 6
                yield (s_x + x, s_y + y, height, x, y, d)
                yield (s_x + x, s_y - y, height, x, y, d)
                yield (s_x - x, s_y + y, height, x, y, d)
                yield (s_x - x, s_y - y, height, x, y, d)
                yield (s_x + y, s_y + x, height, x, y, d)
                yield (s_x + y, s_y - x, height, x, y, d)
                yield (s_x - y, s_y + x, height, x, y, d)
                yield (s_x - y, s_y - x, height, x, y, d)


# Test Cases
print(list(circle_lines(*(54, 52, 8))))

*/

module circle_lines (
    // Function parameters (only need to be set when start is high):
    input wire signed [31:0] s_x,
    input wire signed [31:0] s_y,
    input wire signed [31:0] height,

    input wire _clock, // clock for sync
    input wire _reset, // set high to reset, i.e. done will be high
    input wire _start, // set high to capture inputs (in same cycle) and start generating

    // Implements a ready/valid handshake based on
    // http://www.cjdrake.com/readyvalid-protocol-primer.html
    input wire _ready, // set high when caller is ready for output
    output reg _valid, // is high if output values are valid

    output reg _done, // is high if module done outputting

    // Output values as a tuple with respective index(es)
    output reg signed [31:0] _out0,
    output reg signed [31:0] _out1,
    output reg signed [31:0] _out2,
    output reg signed [31:0] _out3,
    output reg signed [31:0] _out4,
    output reg signed [31:0] _out5
);
    // State variables
    typedef enum{_state_0_while,_state_0_while_0,_state_0_while_1,_state_0_while_2,_state_0_while_3,_state_0_while_4,_state_0_while_5,_state_0_while_6,_state_1,_state_11,_state_11_while,_state_11_while_1,_state_11_while_2,_state_11_while_3,_state_11_while_4,_state_11_while_5,_state_11_while_6,_state_11_while_7,_state_11_while_8,_state_2,_state_3,_state_4,_state_5,_state_6,_state_7,_state_8,_state_9,_state_done} _state_t;
    _state_t _state;
    // Global variables
    reg signed [31:0] _d;
    reg signed [31:0] _y;
    reg signed [31:0] _x;
    reg signed [31:0] _s_x;
    reg signed [31:0] _s_y;
    reg signed [31:0] _height;
    // Core
    always @(posedge _clock) begin
        `ifdef DEBUG
        $display("circle_lines,%s,start:%0d,done:%0d,ready:%0d,valid:%0d,out0:%0d,out1:%0d,out2:%0d,out3:%0d,out4:%0d,out5:%0d", _state.name, _start, _done, _ready, _valid, _out0, _out1, _out2, _out3, _out4, _out5);
        `endif
        _done <= 0;
        if (_ready) begin
            _valid <= 0;
        end
        // Start signal takes precedence over reset
        if (_reset) begin
            _state <= _state_done;
        end
        if (_start) begin
            _s_x <= s_x;
            _s_y <= s_y;
            _height <= height;
            if ($signed(_y >= _x)) begin
                _out0 <= $signed(s_x - _y);
                _out1 <= $signed(s_y - _x);
                _out2 <= height;
                _out3 <= _x;
                _out4 <= _y;
                _out5 <= _d;
                _valid <= 1;
                _state <= _state_11_while_8;
            end else begin
                _out0 <= $signed(s_x - _y);
                _out1 <= $signed(s_y - _x);
                _out2 <= height;
                _out3 <= _x;
                _out4 <= _y;
                _out5 <= _d;
                _valid <= 1;
                _state <= _state_9;
            end
        end else begin
            // If ready or not valid, then continue computation
            if ((_ready || !(_valid))) begin
                case (_state)
                    _state_2: begin
                        _d <= $signed($signed(3) - $signed($signed(2) * _y));
                        _y <= _height;
                        _x <= $signed(0);
                        _done <= 1;
                        _state <= _state_done;
                    end
                    _state_3: begin
                        _out0 <= $signed(_s_x + _x);
                        _out1 <= $signed(_s_y + _y);
                        _out2 <= _height;
                        _out3 <= _x;
                        _out4 <= _y;
                        _out5 <= _d;
                        _valid <= 1;
                        _state <= _state_2;
                    end
                    _state_4: begin
                        _out0 <= $signed(_s_x + _x);
                        _out1 <= $signed(_s_y - _y);
                        _out2 <= _height;
                        _out3 <= _x;
                        _out4 <= _y;
                        _out5 <= _d;
                        _valid <= 1;
                        _state <= _state_3;
                    end
                    _state_5: begin
                        _out0 <= $signed(_s_x - _x);
                        _out1 <= $signed(_s_y + _y);
                        _out2 <= _height;
                        _out3 <= _x;
                        _out4 <= _y;
                        _out5 <= _d;
                        _valid <= 1;
                        _state <= _state_4;
                    end
                    _state_6: begin
                        _out0 <= $signed(_s_x - _x);
                        _out1 <= $signed(_s_y - _y);
                        _out2 <= _height;
                        _out3 <= _x;
                        _out4 <= _y;
                        _out5 <= _d;
                        _valid <= 1;
                        _state <= _state_5;
                    end
                    _state_7: begin
                        _out0 <= $signed(_s_x + _y);
                        _out1 <= $signed(_s_y + _x);
                        _out2 <= _height;
                        _out3 <= _x;
                        _out4 <= _y;
                        _out5 <= _d;
                        _valid <= 1;
                        _state <= _state_6;
                    end
                    _state_8: begin
                        _out0 <= $signed(_s_x + _y);
                        _out1 <= $signed(_s_y - _x);
                        _out2 <= _height;
                        _out3 <= _x;
                        _out4 <= _y;
                        _out5 <= _d;
                        _valid <= 1;
                        _state <= _state_7;
                    end
                    _state_9: begin
                        _out0 <= $signed(_s_x - _y);
                        _out1 <= $signed(_s_y + _x);
                        _out2 <= _height;
                        _out3 <= _x;
                        _out4 <= _y;
                        _out5 <= _d;
                        _valid <= 1;
                        _state <= _state_8;
                    end
                    _state_11_while_1: begin
                        if ($signed(_d > $signed(0))) begin
                            _d <= $signed($signed(_d + $signed($signed(4) * $signed(_x - _y))) + $signed(10));
                            _y <= $signed(_y - $signed(1));
                            _x <= $signed(_x + $signed(1));
                            if ($signed($signed(_y - $signed(1)) >= $signed(_x + $signed(1)))) begin
                                _out0 <= $signed(_s_x - $signed(_y - $signed(1)));
                                _out1 <= $signed(_s_y - $signed(_x + $signed(1)));
                                _out2 <= _height;
                                _out3 <= $signed(_x + $signed(1));
                                _out4 <= $signed(_y - $signed(1));
                                _out5 <= $signed($signed(_d + $signed($signed(4) * $signed(_x - _y))) + $signed(10));
                                _valid <= 1;
                                _state <= _state_11_while_8;
                            end else begin
                                _out0 <= $signed(_s_x - $signed(_y - $signed(1)));
                                _out1 <= $signed(_s_y - $signed(_x + $signed(1)));
                                _out2 <= _height;
                                _out3 <= $signed(_x + $signed(1));
                                _out4 <= $signed(_y - $signed(1));
                                _out5 <= $signed($signed(_d + $signed($signed(4) * $signed(_x - _y))) + $signed(10));
                                _valid <= 1;
                                _state <= _state_9;
                            end
                        end else begin
                            _d <= $signed($signed(_d + $signed($signed(4) * _x)) + $signed(6));
                            _x <= $signed(_x + $signed(1));
                            if ($signed(_y >= $signed(_x + $signed(1)))) begin
                                _out0 <= $signed(_s_x - _y);
                                _out1 <= $signed(_s_y - $signed(_x + $signed(1)));
                                _out2 <= _height;
                                _out3 <= $signed(_x + $signed(1));
                                _out4 <= _y;
                                _out5 <= $signed($signed(_d + $signed($signed(4) * _x)) + $signed(6));
                                _valid <= 1;
                                _state <= _state_11_while_8;
                            end else begin
                                _out0 <= $signed(_s_x - _y);
                                _out1 <= $signed(_s_y - $signed(_x + $signed(1)));
                                _out2 <= _height;
                                _out3 <= $signed(_x + $signed(1));
                                _out4 <= _y;
                                _out5 <= $signed($signed(_d + $signed($signed(4) * _x)) + $signed(6));
                                _valid <= 1;
                                _state <= _state_9;
                            end
                        end
                    end
                    _state_11_while_2: begin
                        _out0 <= $signed(_s_x + _x);
                        _out1 <= $signed(_s_y + _y);
                        _out2 <= _height;
                        _out3 <= _x;
                        _out4 <= _y;
                        _out5 <= _d;
                        _valid <= 1;
                        _state <= _state_11_while_1;
                    end
                    _state_11_while_3: begin
                        _out0 <= $signed(_s_x + _x);
                        _out1 <= $signed(_s_y - _y);
                        _out2 <= _height;
                        _out3 <= _x;
                        _out4 <= _y;
                        _out5 <= _d;
                        _valid <= 1;
                        _state <= _state_11_while_2;
                    end
                    _state_11_while_4: begin
                        _out0 <= $signed(_s_x - _x);
                        _out1 <= $signed(_s_y + _y);
                        _out2 <= _height;
                        _out3 <= _x;
                        _out4 <= _y;
                        _out5 <= _d;
                        _valid <= 1;
                        _state <= _state_11_while_3;
                    end
                    _state_11_while_5: begin
                        _out0 <= $signed(_s_x - _x);
                        _out1 <= $signed(_s_y - _y);
                        _out2 <= _height;
                        _out3 <= _x;
                        _out4 <= _y;
                        _out5 <= _d;
                        _valid <= 1;
                        _state <= _state_11_while_4;
                    end
                    _state_11_while_6: begin
                        _out0 <= $signed(_s_x + _y);
                        _out1 <= $signed(_s_y + _x);
                        _out2 <= _height;
                        _out3 <= _x;
                        _out4 <= _y;
                        _out5 <= _d;
                        _valid <= 1;
                        _state <= _state_11_while_5;
                    end
                    _state_11_while_7: begin
                        _out0 <= $signed(_s_x + _y);
                        _out1 <= $signed(_s_y - _x);
                        _out2 <= _height;
                        _out3 <= _x;
                        _out4 <= _y;
                        _out5 <= _d;
                        _valid <= 1;
                        _state <= _state_11_while_6;
                    end
                    _state_11_while_8: begin
                        _out0 <= $signed(_s_x - _y);
                        _out1 <= $signed(_s_y + _x);
                        _out2 <= _height;
                        _out3 <= _x;
                        _out4 <= _y;
                        _out5 <= _d;
                        _valid <= 1;
                        _state <= _state_11_while_7;
                    end
                    _state_done: begin
                        _done <= 1;
                    end
                endcase
            end
        end
    end
endmodule
/*

# Python Function
        @verilogify(
            namespace=goal_namespace, mode=Modes.OVERWRITE, optimization_level=0
        )
        def triple_circle(centre_x, centre_y, radius):
            # noqa
            c_x = centre_x
            c_y = centre_y
            c_x1 = c_x + radius // 2
            c_y1 = c_y + radius * 2 // 6
            c_x2 = c_x - radius // 2
            c_y2 = c_y + radius * 2 // 6
            c_x3 = c_x
            c_y3 = c_y - radius * 2 // 6

            gen0 = circle_lines(c_x1, c_y1, radius)
            for x, y, a, b, c, d in gen0:
                yield x, y
            # gen1 = circle_lines(c_x2, c_y2, radius)
            # for x, y, a, b, c, d in gen1:
            #     yield x, y
            # gen2 = circle_lines(c_x3, c_y3, radius)
            # for x, y, a, b, c, d in gen2:
            #     yield x, y


# Test Cases
print(list(triple_circle(*(50, 50, 8))))

*/

module triple_circle (
    // Function parameters (only need to be set when start is high):
    input wire signed [31:0] centre_x,
    input wire signed [31:0] centre_y,
    input wire signed [31:0] radius,

    input wire _clock, // clock for sync
    input wire _reset, // set high to reset, i.e. done will be high
    input wire _start, // set high to capture inputs (in same cycle) and start generating

    // Implements a ready/valid handshake based on
    // http://www.cjdrake.com/readyvalid-protocol-primer.html
    input wire _ready, // set high when caller is ready for output
    output reg _valid, // is high if output values are valid

    output reg _done, // is high if module done outputting

    // Output values as a tuple with respective index(es)
    output reg signed [31:0] _out0,
    output reg signed [31:0] _out1
);
    // State variables
    typedef enum{_state_0,_state_0_for_0,_state_0_for_body_0,_state_1,_state_1_call_0,_state_2,_state_3,_state_4,_state_5,_state_6,_state_7,_state_8,_state_8_call_0,_state_9,_state_9_for_0,_state_9_for_body_0,_state_done} _state_t;
    _state_t _state;
    // Global variables
    reg signed [31:0] _x;
    reg signed [31:0] _y;
    reg signed [31:0] _a;
    reg signed [31:0] _b;
    reg signed [31:0] _c;
    reg signed [31:0] _d;
    reg signed [31:0] _c_y3;
    reg signed [31:0] _c_x3;
    reg signed [31:0] _c_y2;
    reg signed [31:0] _c_x2;
    reg signed [31:0] _c_y1;
    reg signed [31:0] _c_x1;
    reg signed [31:0] _c_y;
    reg signed [31:0] _c_x;
    reg signed [31:0] _centre_x;
    reg signed [31:0] _centre_y;
    reg signed [31:0] _radius;
    // ================ Function Instance ================
    reg [31:0] _gen0_circle_lines_s_x;
    reg [31:0] _gen0_circle_lines_s_y;
    reg [31:0] _gen0_circle_lines_height;
    wire [31:0] _gen0_circle_lines_out0;
    wire [31:0] _gen0_circle_lines_out1;
    wire [31:0] _gen0_circle_lines_out2;
    wire [31:0] _gen0_circle_lines_out3;
    wire [31:0] _gen0_circle_lines_out4;
    wire [31:0] _gen0_circle_lines_out5;
    wire _gen0_circle_lines__valid;
    wire _gen0_circle_lines__done;
    reg _gen0_circle_lines__start;
    reg _gen0_circle_lines__ready;
    circle_lines _gen0 (
        .s_x(_gen0_circle_lines_s_x),
        .s_y(_gen0_circle_lines_s_y),
        .height(_gen0_circle_lines_height),
        ._out0(_gen0_circle_lines_out0),
        ._out1(_gen0_circle_lines_out1),
        ._out2(_gen0_circle_lines_out2),
        ._out3(_gen0_circle_lines_out3),
        ._out4(_gen0_circle_lines_out4),
        ._out5(_gen0_circle_lines_out5),
        ._valid(_gen0_circle_lines__valid),
        ._done(_gen0_circle_lines__done),
        ._clock(_clock),
        ._start(_gen0_circle_lines__start),
        ._reset(_reset),
        ._ready(_gen0_circle_lines__ready)
        );
    // Core
    always @(posedge _clock) begin
        `ifdef DEBUG
        $display("triple_circle,%s,start:%0d,done:%0d,ready:%0d,valid:%0d,out0:%0d,out1:%0d", _state.name, _start, _done, _ready, _valid, _out0, _out1);
        `endif
        _done <= 0;
        if (_ready) begin
            _valid <= 0;
        end
        // Start signal takes precedence over reset
        if (_reset) begin
            _state <= _state_done;
        end
        if (_start) begin
            _centre_x <= centre_x;
            _centre_y <= centre_y;
            _radius <= radius;
            _state <= _state_9;
        end else begin
            // If ready or not valid, then continue computation
            if ((_ready || !(_valid))) begin
                case (_state)
                    _state_done: begin
                        _done <= 1;
                        _state <= _state_done;
                    end
                    _state_0_for_body_0: begin
                        _out0 <= _x;
                        _out1 <= _y;
                        _valid <= 1;
                        _state <= _state_0_for_0;
                    end
                    _state_0_for_0: begin
                        _gen0_circle_lines__ready <= 1;
                        _gen0_circle_lines__start <= 0;
                        if ((_gen0_circle_lines__ready && _gen0_circle_lines__valid)) begin
                            _gen0_circle_lines__ready <= 0;
                            _x <= _gen0_circle_lines_out0;
                            _y <= _gen0_circle_lines_out1;
                            _a <= _gen0_circle_lines_out2;
                            _b <= _gen0_circle_lines_out3;
                            _c <= _gen0_circle_lines_out4;
                            _d <= _gen0_circle_lines_out5;
                            if (_gen0_circle_lines__done) begin
                                _state <= _state_done;
                            end else begin
                                _state <= _state_0_for_body_0;
                            end
                        end else begin
                            if (_gen0_circle_lines__done) begin
                                _state <= _state_done;
                            end else begin
                                _state <= _state_0_for_0;
                            end
                        end
                    end
                    _state_1_call_0: begin
                        _gen0_circle_lines__ready <= 0;
                        _gen0_circle_lines__start <= 1;
                        _gen0_circle_lines_s_x <= _c_x1;
                        _gen0_circle_lines_s_y <= _c_y1;
                        _gen0_circle_lines_height <= _radius;
                        _state <= _state_0_for_0;
                    end
                    _state_2: begin
                        _c_y3 <= $signed(_c_y - ($signed($signed($signed(_radius * $signed(2)) % $signed(6)) === $signed(0)) ? $signed($signed(_radius * $signed(2)) / $signed(6)) : $signed($signed($signed(_radius * $signed(2)) / $signed(6)) - $signed(($signed($signed(_radius * $signed(2)) < $signed(0)) ^ $signed($signed(6) < $signed(0))) & $signed(1)))));
                        _state <= _state_1_call_0;
                    end
                    _state_3: begin
                        _c_x3 <= _c_x;
                        _state <= _state_2;
                    end
                    _state_4: begin
                        _c_y2 <= $signed(_c_y + ($signed($signed($signed(_radius * $signed(2)) % $signed(6)) === $signed(0)) ? $signed($signed(_radius * $signed(2)) / $signed(6)) : $signed($signed($signed(_radius * $signed(2)) / $signed(6)) - $signed(($signed($signed(_radius * $signed(2)) < $signed(0)) ^ $signed($signed(6) < $signed(0))) & $signed(1)))));
                        _state <= _state_3;
                    end
                    _state_5: begin
                        _c_x2 <= $signed(_c_x - ($signed($signed(_radius % $signed(2)) === $signed(0)) ? $signed(_radius / $signed(2)) : $signed($signed(_radius / $signed(2)) - $signed(($signed(_radius < $signed(0)) ^ $signed($signed(2) < $signed(0))) & $signed(1)))));
                        _state <= _state_4;
                    end
                    _state_6: begin
                        _c_y1 <= $signed(_c_y + ($signed($signed($signed(_radius * $signed(2)) % $signed(6)) === $signed(0)) ? $signed($signed(_radius * $signed(2)) / $signed(6)) : $signed($signed($signed(_radius * $signed(2)) / $signed(6)) - $signed(($signed($signed(_radius * $signed(2)) < $signed(0)) ^ $signed($signed(6) < $signed(0))) & $signed(1)))));
                        _state <= _state_5;
                    end
                    _state_7: begin
                        _c_x1 <= $signed(_c_x + ($signed($signed(_radius % $signed(2)) === $signed(0)) ? $signed(_radius / $signed(2)) : $signed($signed(_radius / $signed(2)) - $signed(($signed(_radius < $signed(0)) ^ $signed($signed(2) < $signed(0))) & $signed(1)))));
                        _state <= _state_6;
                    end
                    _state_8: begin
                        _c_y <= _centre_y;
                        _state <= _state_7;
                    end
                    _state_9: begin
                        _c_x <= _centre_x;
                        _state <= _state_8;
                    end
                    _state_done: begin
                        _done <= 1;
                    end
                endcase
            end
        end
    end
endmodule
