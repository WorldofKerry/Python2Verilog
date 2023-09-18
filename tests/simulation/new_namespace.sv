/*

# Python Function
        @verilogify(
            namespace=goal_namespace, mode=Modes.OVERWRITE, optimization_level=1
        )
        def circle_lines(s_x, s_y, height) -> tuple[int, int, int, int, int, int]:
            x = 0
            y = height
            d = 3 - 2 * y
            yield (s_x + x, s_y + y)
            yield (s_x + x, s_y - y)
            yield (s_x - x, s_y + y)
            yield (s_x - x, s_y - y)
            yield (s_x + y, s_y + x)
            yield (s_x + y, s_y - x)
            yield (s_x - y, s_y + x)
            yield (s_x - y, s_y - x)
            while y >= x:
                x = x + 1
                if d > 0:
                    y = y - 1
                    d = d + 4 * (x - y) + 10
                else:
                    d = d + 4 * x + 6
                yield (s_x + x, s_y + y)
                yield (s_x + x, s_y - y)
                yield (s_x - x, s_y + y)
                yield (s_x - x, s_y - y)
                yield (s_x + y, s_y + x)
                yield (s_x + y, s_y - x)
                yield (s_x - y, s_y + x)
                yield (s_x - y, s_y - x)


# Test Cases
print(list(circle_lines(*(54, 52, 8))))
print(list(circle_lines(*(46, 52, 8))))
print(list(circle_lines(*(50, 48, 8))))
print(list(circle_lines(*(54, 52, 8))))
print(list(circle_lines(*(46, 52, 8))))
print(list(circle_lines(*(50, 48, 8))))

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
    output reg signed [31:0] _out1
);
    // State variables
    typedef enum{_state_0_while,_state_0_while_0,_state_0_while_1,_state_0_while_2,_state_0_while_3,_state_0_while_4,_state_0_while_5,_state_0_while_6,_state_1,_state_11,_state_11_while,_state_11_while_1,_state_11_while_2,_state_11_while_3,_state_11_while_4,_state_11_while_5,_state_11_while_6,_state_11_while_7,_state_11_while_8,_state_2,_state_3,_state_4,_state_5,_state_6,_state_7,_state_8,_state_9,_state_done,_state_idle} _state_t;
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
        $display("circle_lines,%s,_start=%0d,_done=%0d,_ready=%0d,_valid=%0d,s_x=%0d,s_y=%0d,height=%0d,_s_x=%0d,_s_y=%0d,_height=%0d,_out0=%0d,_out1=%0d,_d=%0d,_y=%0d,_x=%0d", _state.name, _start, _done, _ready, _valid, s_x, s_y, height, _s_x, _s_y, _height, _out0, _out1, _d, _y, _x);
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
            _s_x <= s_x;
            _s_y <= s_y;
            _height <= height;
            if ($signed(_y >= _x)) begin
                _out0 <= $signed(s_x - _y);
                _out1 <= $signed(s_y - _x);
                _valid <= 1;
                _state <= _state_11_while_8;
            end else begin
                _out0 <= $signed(s_x - _y);
                _out1 <= $signed(s_y - _x);
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
                        if ($signed(!(_valid) && _ready)) begin
                            _done <= 1;
                            _state <= _state_idle;
                        end else begin
                            _state <= _state_done;
                        end
                    end
                    _state_3: begin
                        _out0 <= $signed(_s_x + _x);
                        _out1 <= $signed(_s_y + _y);
                        _valid <= 1;
                        _state <= _state_2;
                    end
                    _state_4: begin
                        _out0 <= $signed(_s_x + _x);
                        _out1 <= $signed(_s_y - _y);
                        _valid <= 1;
                        _state <= _state_3;
                    end
                    _state_5: begin
                        _out0 <= $signed(_s_x - _x);
                        _out1 <= $signed(_s_y + _y);
                        _valid <= 1;
                        _state <= _state_4;
                    end
                    _state_6: begin
                        _out0 <= $signed(_s_x - _x);
                        _out1 <= $signed(_s_y - _y);
                        _valid <= 1;
                        _state <= _state_5;
                    end
                    _state_7: begin
                        _out0 <= $signed(_s_x + _y);
                        _out1 <= $signed(_s_y + _x);
                        _valid <= 1;
                        _state <= _state_6;
                    end
                    _state_8: begin
                        _out0 <= $signed(_s_x + _y);
                        _out1 <= $signed(_s_y - _x);
                        _valid <= 1;
                        _state <= _state_7;
                    end
                    _state_9: begin
                        _out0 <= $signed(_s_x - _y);
                        _out1 <= $signed(_s_y + _x);
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
                                _valid <= 1;
                                _state <= _state_11_while_8;
                            end else begin
                                _out0 <= $signed(_s_x - $signed(_y - $signed(1)));
                                _out1 <= $signed(_s_y - $signed(_x + $signed(1)));
                                _valid <= 1;
                                _state <= _state_9;
                            end
                        end else begin
                            _d <= $signed($signed(_d + $signed($signed(4) * _x)) + $signed(6));
                            _x <= $signed(_x + $signed(1));
                            if ($signed(_y >= $signed(_x + $signed(1)))) begin
                                _out0 <= $signed(_s_x - _y);
                                _out1 <= $signed(_s_y - $signed(_x + $signed(1)));
                                _valid <= 1;
                                _state <= _state_11_while_8;
                            end else begin
                                _out0 <= $signed(_s_x - _y);
                                _out1 <= $signed(_s_y - $signed(_x + $signed(1)));
                                _valid <= 1;
                                _state <= _state_9;
                            end
                        end
                    end
                    _state_11_while_2: begin
                        _out0 <= $signed(_s_x + _x);
                        _out1 <= $signed(_s_y + _y);
                        _valid <= 1;
                        _state <= _state_11_while_1;
                    end
                    _state_11_while_3: begin
                        _out0 <= $signed(_s_x + _x);
                        _out1 <= $signed(_s_y - _y);
                        _valid <= 1;
                        _state <= _state_11_while_2;
                    end
                    _state_11_while_4: begin
                        _out0 <= $signed(_s_x - _x);
                        _out1 <= $signed(_s_y + _y);
                        _valid <= 1;
                        _state <= _state_11_while_3;
                    end
                    _state_11_while_5: begin
                        _out0 <= $signed(_s_x - _x);
                        _out1 <= $signed(_s_y - _y);
                        _valid <= 1;
                        _state <= _state_11_while_4;
                    end
                    _state_11_while_6: begin
                        _out0 <= $signed(_s_x + _y);
                        _out1 <= $signed(_s_y + _x);
                        _valid <= 1;
                        _state <= _state_11_while_5;
                    end
                    _state_11_while_7: begin
                        _out0 <= $signed(_s_x + _y);
                        _out1 <= $signed(_s_y - _x);
                        _valid <= 1;
                        _state <= _state_11_while_6;
                    end
                    _state_11_while_8: begin
                        _out0 <= $signed(_s_x - _y);
                        _out1 <= $signed(_s_y + _x);
                        _valid <= 1;
                        _state <= _state_11_while_7;
                    end
                    _state_done: begin
                        if ($signed(!(_valid) && _ready)) begin
                            _done <= 1;
                            _state <= _state_idle;
                        end else begin
                            _state <= _state_done;
                        end
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
            for x, y in gen0:
                yield x, y
            gen1 = circle_lines(c_x2, c_y2, radius)
            for x, y in gen1:
                yield x, y
            # reuse
            gen0 = circle_lines(c_x3, c_y3, radius)
            for x, y in gen0:
                yield x, y


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
    typedef enum{_state_0,_state_0_for_0,_state_0_for_body_0,_state_1,_state_10,_state_10_call_0,_state_11,_state_11_for_0,_state_11_for_body_0,_state_12,_state_12_call_0,_state_13,_state_13_for_0,_state_13_for_body_0,_state_1_call_0,_state_2,_state_2_for_0,_state_2_for_body_0,_state_3,_state_3_call_0,_state_4,_state_4_for_0,_state_4_for_body_0,_state_5,_state_5_call_0,_state_6,_state_7,_state_8,_state_8_call_0,_state_9,_state_9_for_0,_state_9_for_body_0,_state_done,_state_idle} _state_t;
    _state_t _state;
    // Global variables
    reg signed [31:0] _x;
    reg signed [31:0] _y;
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
        ._valid(_gen0_circle_lines__valid),
        ._done(_gen0_circle_lines__done),
        ._clock(_clock),
        ._start(_gen0_circle_lines__start),
        ._reset(_reset),
        ._ready(_gen0_circle_lines__ready)
        );
    // ================ Function Instance ================
    reg [31:0] _gen1_circle_lines_s_x;
    reg [31:0] _gen1_circle_lines_s_y;
    reg [31:0] _gen1_circle_lines_height;
    wire [31:0] _gen1_circle_lines_out0;
    wire [31:0] _gen1_circle_lines_out1;
    wire _gen1_circle_lines__valid;
    wire _gen1_circle_lines__done;
    reg _gen1_circle_lines__start;
    reg _gen1_circle_lines__ready;
    circle_lines _gen1 (
        .s_x(_gen1_circle_lines_s_x),
        .s_y(_gen1_circle_lines_s_y),
        .height(_gen1_circle_lines_height),
        ._out0(_gen1_circle_lines_out0),
        ._out1(_gen1_circle_lines_out1),
        ._valid(_gen1_circle_lines__valid),
        ._done(_gen1_circle_lines__done),
        ._clock(_clock),
        ._start(_gen1_circle_lines__start),
        ._reset(_reset),
        ._ready(_gen1_circle_lines__ready)
        );
    // Core
    always @(posedge _clock) begin
        `ifdef DEBUG
        $display("triple_circle,%s,_start=%0d,_done=%0d,_ready=%0d,_valid=%0d,centre_x=%0d,centre_y=%0d,radius=%0d,_centre_x=%0d,_centre_y=%0d,_radius=%0d,_out0=%0d,_out1=%0d,_x=%0d,_y=%0d,_c_y3=%0d,_c_x3=%0d,_c_y2=%0d,_c_x2=%0d,_c_y1=%0d,_c_x1=%0d,_c_y=%0d,_c_x=%0d", _state.name, _start, _done, _ready, _valid, centre_x, centre_y, radius, _centre_x, _centre_y, _radius, _out0, _out1, _x, _y, _c_y3, _c_x3, _c_y2, _c_x2, _c_y1, _c_x1, _c_y, _c_x);
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
            _centre_x <= centre_x;
            _centre_y <= centre_y;
            _radius <= radius;
            _state <= _state_13_for_0;
        end else begin
            // If ready or not valid, then continue computation
            if ((_ready || !(_valid))) begin
                case (_state)
                    _state_done: begin
                        if ($signed(!(_valid) && _ready)) begin
                            _done <= 1;
                            _state <= _state_idle;
                        end else begin
                            _state <= _state_done;
                        end
                    end
                    _state_0: begin
                        _c_x <= _centre_x;
                        _state <= _state_done;
                    end
                    _state_1: begin
                        _c_y <= _centre_y;
                        _state <= _state_0;
                    end
                    _state_2: begin
                        _c_x1 <= $signed(_c_x + ($signed($signed(_radius % $signed(2)) === $signed(0)) ? $signed(_radius / $signed(2)) : $signed($signed(_radius / $signed(2)) - $signed(($signed(_radius < $signed(0)) ^ $signed($signed(2) < $signed(0))) & $signed(1)))));
                        _state <= _state_1;
                    end
                    _state_3: begin
                        _c_y1 <= $signed(_c_y + ($signed($signed($signed(_radius * $signed(2)) % $signed(6)) === $signed(0)) ? $signed($signed(_radius * $signed(2)) / $signed(6)) : $signed($signed($signed(_radius * $signed(2)) / $signed(6)) - $signed(($signed($signed(_radius * $signed(2)) < $signed(0)) ^ $signed($signed(6) < $signed(0))) & $signed(1)))));
                        _state <= _state_2;
                    end
                    _state_4: begin
                        _c_x2 <= $signed(_c_x - ($signed($signed(_radius % $signed(2)) === $signed(0)) ? $signed(_radius / $signed(2)) : $signed($signed(_radius / $signed(2)) - $signed(($signed(_radius < $signed(0)) ^ $signed($signed(2) < $signed(0))) & $signed(1)))));
                        _state <= _state_3;
                    end
                    _state_5: begin
                        _c_y2 <= $signed(_c_y + ($signed($signed($signed(_radius * $signed(2)) % $signed(6)) === $signed(0)) ? $signed($signed(_radius * $signed(2)) / $signed(6)) : $signed($signed($signed(_radius * $signed(2)) / $signed(6)) - $signed(($signed($signed(_radius * $signed(2)) < $signed(0)) ^ $signed($signed(6) < $signed(0))) & $signed(1)))));
                        _state <= _state_4;
                    end
                    _state_6: begin
                        _c_x3 <= _c_x;
                        _state <= _state_5;
                    end
                    _state_7: begin
                        _c_y3 <= $signed(_c_y - ($signed($signed($signed(_radius * $signed(2)) % $signed(6)) === $signed(0)) ? $signed($signed(_radius * $signed(2)) / $signed(6)) : $signed($signed($signed(_radius * $signed(2)) / $signed(6)) - $signed(($signed($signed(_radius * $signed(2)) < $signed(0)) ^ $signed($signed(6) < $signed(0))) & $signed(1)))));
                        _state <= _state_6;
                    end
                    _state_8_call_0: begin
                        _gen0_circle_lines__ready <= 0;
                        _gen0_circle_lines__start <= 1;
                        _gen0_circle_lines_s_x <= _c_x1;
                        _gen0_circle_lines_s_y <= _c_y1;
                        _gen0_circle_lines_height <= _radius;
                        _state <= _state_7;
                    end
                    _state_9_for_body_0: begin
                        _out0 <= _x;
                        _out1 <= _y;
                        _valid <= 1;
                        _state <= _state_9_for_0;
                    end
                    _state_9_for_0: begin
                        _gen0_circle_lines__ready <= 1;
                        _gen0_circle_lines__start <= 0;
                        if ((_gen0_circle_lines__ready && _gen0_circle_lines__valid)) begin
                            _gen0_circle_lines__ready <= 0;
                            _x <= _gen0_circle_lines_out0;
                            _y <= _gen0_circle_lines_out1;
                            if (_gen0_circle_lines__done) begin
                                _state <= _state_8_call_0;
                            end else begin
                                _state <= _state_9_for_body_0;
                            end
                        end else begin
                            if (_gen0_circle_lines__done) begin
                                _state <= _state_8_call_0;
                            end else begin
                                _state <= _state_9_for_0;
                            end
                        end
                    end
                    _state_10_call_0: begin
                        _gen1_circle_lines__ready <= 0;
                        _gen1_circle_lines__start <= 1;
                        _gen1_circle_lines_s_x <= _c_x2;
                        _gen1_circle_lines_s_y <= _c_y2;
                        _gen1_circle_lines_height <= _radius;
                        _state <= _state_9_for_0;
                    end
                    _state_11_for_body_0: begin
                        _out0 <= _x;
                        _out1 <= _y;
                        _valid <= 1;
                        _state <= _state_11_for_0;
                    end
                    _state_11_for_0: begin
                        _gen1_circle_lines__ready <= 1;
                        _gen1_circle_lines__start <= 0;
                        if ((_gen1_circle_lines__ready && _gen1_circle_lines__valid)) begin
                            _gen1_circle_lines__ready <= 0;
                            _x <= _gen1_circle_lines_out0;
                            _y <= _gen1_circle_lines_out1;
                            if (_gen1_circle_lines__done) begin
                                _state <= _state_10_call_0;
                            end else begin
                                _state <= _state_11_for_body_0;
                            end
                        end else begin
                            if (_gen1_circle_lines__done) begin
                                _state <= _state_10_call_0;
                            end else begin
                                _state <= _state_11_for_0;
                            end
                        end
                    end
                    _state_12_call_0: begin
                        _gen0_circle_lines__ready <= 0;
                        _gen0_circle_lines__start <= 1;
                        _gen0_circle_lines_s_x <= _c_x3;
                        _gen0_circle_lines_s_y <= _c_y3;
                        _gen0_circle_lines_height <= _radius;
                        _state <= _state_11_for_0;
                    end
                    _state_13_for_body_0: begin
                        _out0 <= _x;
                        _out1 <= _y;
                        _valid <= 1;
                        _state <= _state_13_for_0;
                    end
                    _state_13_for_0: begin
                        _gen0_circle_lines__ready <= 1;
                        _gen0_circle_lines__start <= 0;
                        if ((_gen0_circle_lines__ready && _gen0_circle_lines__valid)) begin
                            _gen0_circle_lines__ready <= 0;
                            _x <= _gen0_circle_lines_out0;
                            _y <= _gen0_circle_lines_out1;
                            if (_gen0_circle_lines__done) begin
                                _state <= _state_12_call_0;
                            end else begin
                                _state <= _state_13_for_body_0;
                            end
                        end else begin
                            if (_gen0_circle_lines__done) begin
                                _state <= _state_12_call_0;
                            end else begin
                                _state <= _state_13_for_0;
                            end
                        end
                    end
                endcase
            end
        end
    end
endmodule
