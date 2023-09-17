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
    output reg signed [31:0] _0,
    output reg signed [31:0] _1,
    output reg signed [31:0] _2,
    output reg signed [31:0] _3,
    output reg signed [31:0] _4,
    output reg signed [31:0] _5
);
    localparam _state_0_while = 0;
    localparam _state_0_while_0 = 1;
    localparam _state_0_while_1 = 2;
    localparam _state_0_while_2 = 3;
    localparam _state_0_while_3 = 4;
    localparam _state_0_while_4 = 5;
    localparam _state_0_while_5 = 6;
    localparam _state_0_while_6 = 7;
    localparam _state_1 = 8;
    localparam _state_11 = 9;
    localparam _state_11_while = 10;
    localparam _state_11_while_1 = 11;
    localparam _state_11_while_2 = 12;
    localparam _state_11_while_3 = 13;
    localparam _state_11_while_4 = 14;
    localparam _state_11_while_5 = 15;
    localparam _state_11_while_6 = 16;
    localparam _state_11_while_7 = 17;
    localparam _state_11_while_8 = 18;
    localparam _state_2 = 19;
    localparam _state_3 = 20;
    localparam _state_4 = 21;
    localparam _state_5 = 22;
    localparam _state_6 = 23;
    localparam _state_7 = 24;
    localparam _state_8 = 25;
    localparam _state_9 = 26;
    localparam _state_done = 27;
    // Global variables
    reg signed [31:0] _d;
    reg signed [31:0] _y;
    reg signed [31:0] _x;
    reg signed [31:0] _state;
    reg signed [31:0] _s_x;
    reg signed [31:0] _s_y;
    reg signed [31:0] _height;
    // Core
    always @(posedge _clock) begin
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
                _0 <= $signed(s_x - _y);
                _1 <= $signed(s_y - _x);
                _2 <= height;
                _3 <= _x;
                _4 <= _y;
                _5 <= _d;
                _valid <= 1;
                _state <= _state_11_while_8;
            end else begin
                _0 <= $signed(s_x - _y);
                _1 <= $signed(s_y - _x);
                _2 <= height;
                _3 <= _x;
                _4 <= _y;
                _5 <= _d;
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
                        _0 <= $signed(_s_x + _x);
                        _1 <= $signed(_s_y + _y);
                        _2 <= _height;
                        _3 <= _x;
                        _4 <= _y;
                        _5 <= _d;
                        _valid <= 1;
                        _state <= _state_2;
                    end
                    _state_4: begin
                        _0 <= $signed(_s_x + _x);
                        _1 <= $signed(_s_y - _y);
                        _2 <= _height;
                        _3 <= _x;
                        _4 <= _y;
                        _5 <= _d;
                        _valid <= 1;
                        _state <= _state_3;
                    end
                    _state_5: begin
                        _0 <= $signed(_s_x - _x);
                        _1 <= $signed(_s_y + _y);
                        _2 <= _height;
                        _3 <= _x;
                        _4 <= _y;
                        _5 <= _d;
                        _valid <= 1;
                        _state <= _state_4;
                    end
                    _state_6: begin
                        _0 <= $signed(_s_x - _x);
                        _1 <= $signed(_s_y - _y);
                        _2 <= _height;
                        _3 <= _x;
                        _4 <= _y;
                        _5 <= _d;
                        _valid <= 1;
                        _state <= _state_5;
                    end
                    _state_7: begin
                        _0 <= $signed(_s_x + _y);
                        _1 <= $signed(_s_y + _x);
                        _2 <= _height;
                        _3 <= _x;
                        _4 <= _y;
                        _5 <= _d;
                        _valid <= 1;
                        _state <= _state_6;
                    end
                    _state_8: begin
                        _0 <= $signed(_s_x + _y);
                        _1 <= $signed(_s_y - _x);
                        _2 <= _height;
                        _3 <= _x;
                        _4 <= _y;
                        _5 <= _d;
                        _valid <= 1;
                        _state <= _state_7;
                    end
                    _state_9: begin
                        _0 <= $signed(_s_x - _y);
                        _1 <= $signed(_s_y + _x);
                        _2 <= _height;
                        _3 <= _x;
                        _4 <= _y;
                        _5 <= _d;
                        _valid <= 1;
                        _state <= _state_8;
                    end
                    _state_11_while_1: begin
                        if ($signed(_d > $signed(0))) begin
                            _d <= $signed($signed(_d + $signed($signed(4) * $signed(_x - _y))) + $signed(10));
                            _y <= $signed(_y - $signed(1));
                            _x <= $signed(_x + $signed(1));
                            if ($signed($signed(_y - $signed(1)) >= $signed(_x + $signed(1)))) begin
                                _0 <= $signed(_s_x - $signed(_y - $signed(1)));
                                _1 <= $signed(_s_y - $signed(_x + $signed(1)));
                                _2 <= _height;
                                _3 <= $signed(_x + $signed(1));
                                _4 <= $signed(_y - $signed(1));
                                _5 <= $signed($signed(_d + $signed($signed(4) * $signed(_x - _y))) + $signed(10));
                                _valid <= 1;
                                _state <= _state_11_while_8;
                            end else begin
                                _0 <= $signed(_s_x - $signed(_y - $signed(1)));
                                _1 <= $signed(_s_y - $signed(_x + $signed(1)));
                                _2 <= _height;
                                _3 <= $signed(_x + $signed(1));
                                _4 <= $signed(_y - $signed(1));
                                _5 <= $signed($signed(_d + $signed($signed(4) * $signed(_x - _y))) + $signed(10));
                                _valid <= 1;
                                _state <= _state_9;
                            end
                        end else begin
                            _d <= $signed($signed(_d + $signed($signed(4) * _x)) + $signed(6));
                            _x <= $signed(_x + $signed(1));
                            if ($signed(_y >= $signed(_x + $signed(1)))) begin
                                _0 <= $signed(_s_x - _y);
                                _1 <= $signed(_s_y - $signed(_x + $signed(1)));
                                _2 <= _height;
                                _3 <= $signed(_x + $signed(1));
                                _4 <= _y;
                                _5 <= $signed($signed(_d + $signed($signed(4) * _x)) + $signed(6));
                                _valid <= 1;
                                _state <= _state_11_while_8;
                            end else begin
                                _0 <= $signed(_s_x - _y);
                                _1 <= $signed(_s_y - $signed(_x + $signed(1)));
                                _2 <= _height;
                                _3 <= $signed(_x + $signed(1));
                                _4 <= _y;
                                _5 <= $signed($signed(_d + $signed($signed(4) * _x)) + $signed(6));
                                _valid <= 1;
                                _state <= _state_9;
                            end
                        end
                    end
                    _state_11_while_2: begin
                        _0 <= $signed(_s_x + _x);
                        _1 <= $signed(_s_y + _y);
                        _2 <= _height;
                        _3 <= _x;
                        _4 <= _y;
                        _5 <= _d;
                        _valid <= 1;
                        _state <= _state_11_while_1;
                    end
                    _state_11_while_3: begin
                        _0 <= $signed(_s_x + _x);
                        _1 <= $signed(_s_y - _y);
                        _2 <= _height;
                        _3 <= _x;
                        _4 <= _y;
                        _5 <= _d;
                        _valid <= 1;
                        _state <= _state_11_while_2;
                    end
                    _state_11_while_4: begin
                        _0 <= $signed(_s_x - _x);
                        _1 <= $signed(_s_y + _y);
                        _2 <= _height;
                        _3 <= _x;
                        _4 <= _y;
                        _5 <= _d;
                        _valid <= 1;
                        _state <= _state_11_while_3;
                    end
                    _state_11_while_5: begin
                        _0 <= $signed(_s_x - _x);
                        _1 <= $signed(_s_y - _y);
                        _2 <= _height;
                        _3 <= _x;
                        _4 <= _y;
                        _5 <= _d;
                        _valid <= 1;
                        _state <= _state_11_while_4;
                    end
                    _state_11_while_6: begin
                        _0 <= $signed(_s_x + _y);
                        _1 <= $signed(_s_y + _x);
                        _2 <= _height;
                        _3 <= _x;
                        _4 <= _y;
                        _5 <= _d;
                        _valid <= 1;
                        _state <= _state_11_while_5;
                    end
                    _state_11_while_7: begin
                        _0 <= $signed(_s_x + _y);
                        _1 <= $signed(_s_y - _x);
                        _2 <= _height;
                        _3 <= _x;
                        _4 <= _y;
                        _5 <= _d;
                        _valid <= 1;
                        _state <= _state_11_while_6;
                    end
                    _state_11_while_8: begin
                        _0 <= $signed(_s_x - _y);
                        _1 <= $signed(_s_y + _x);
                        _2 <= _height;
                        _3 <= _x;
                        _4 <= _y;
                        _5 <= _d;
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
    output reg signed [31:0] _0,
    output reg signed [31:0] _1
);
    localparam _state_0 = 0;
    localparam _state_0_call_0 = 1;
    localparam _state_0_for_0 = 2;
    localparam _state_1 = 3;
    localparam _state_1_call_0 = 4;
    localparam _state_2 = 5;
    localparam _state_3 = 6;
    localparam _state_4 = 7;
    localparam _state_5 = 8;
    localparam _state_6 = 9;
    localparam _state_7 = 10;
    localparam _state_8 = 11;
    localparam _state_8_call_0 = 12;
    localparam _state_9 = 13;
    localparam _state_9_call_0 = 14;
    localparam _state_9_for_0 = 15;
    localparam _state_done = 16;
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
    reg signed [31:0] _state;
    reg signed [31:0] _centre_x;
    reg signed [31:0] _centre_y;
    reg signed [31:0] _radius;
    // ================ Function Instance ================
    reg [31:0] _gen0_circle_lines_s_x;
    reg [31:0] _gen0_circle_lines_s_y;
    reg [31:0] _gen0_circle_lines_height;
    wire [31:0] _gen0_circle_lines_0;
    wire [31:0] _gen0_circle_lines_1;
    wire [31:0] _gen0_circle_lines_2;
    wire [31:0] _gen0_circle_lines_3;
    wire [31:0] _gen0_circle_lines_4;
    wire [31:0] _gen0_circle_lines_5;
    wire _gen0_circle_lines__valid;
    wire _gen0_circle_lines__done;
    reg _gen0_circle_lines__start;
    reg _gen0_circle_lines__ready;
    circle_lines _gen0 (
        .s_x(_gen0_circle_lines_s_x),
        .s_y(_gen0_circle_lines_s_y),
        .height(_gen0_circle_lines_height),
        ._0(_gen0_circle_lines_0),
        ._1(_gen0_circle_lines_1),
        ._2(_gen0_circle_lines_2),
        ._3(_gen0_circle_lines_3),
        ._4(_gen0_circle_lines_4),
        ._5(_gen0_circle_lines_5),
        ._valid(_gen0_circle_lines__valid),
        ._done(_gen0_circle_lines__done),
        ._clock(_clock),
        ._start(_gen0_circle_lines__start),
        ._reset(_reset),
        ._ready(_gen0_circle_lines__ready)
        );
    // Core
    always @(posedge _clock) begin
        // $display("state %0d, callee %0d %0d", _state, _gen0_circle_lines_0, _gen0_circle_lines_1);
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
                    _state_0_for_0: begin
                        _0 <= _x;
                        _1 <= _y;
                        _valid <= 1;
                        _state <= _state_0_call_0;
                    end
                    _state_0_call_0: begin
                        $display("Called %0d %0d %0d, state %0d, output %0d", _gen0_circle_lines__ready, _gen0_circle_lines__start, _gen0_circle_lines_s_x, _gen0._state, _gen0_circle_lines_0);
                        _gen0_circle_lines__ready <= 1;
                        _gen0_circle_lines__start <= 0;
                        $display("valid %0d", _gen0_circle_lines__valid);
                        if ((_gen0_circle_lines__ready && _gen0_circle_lines__valid)) begin
                            _gen0_circle_lines__ready <= 0;
                            _x <= _gen0_circle_lines_0;
                            _y <= _gen0_circle_lines_1;
                            _a <= _gen0_circle_lines_2;
                            _b <= _gen0_circle_lines_3;
                            _c <= _gen0_circle_lines_4;
                            _d <= _gen0_circle_lines_5;
                            if (_gen0_circle_lines__done) begin
                                _state <= _state_done;
                            end else begin
                                _state <= _state_0_for_0;
                            end
                        end else begin
                            if (_gen0_circle_lines__done) begin
                                _state <= _state_done;
                            end else begin
                                _state <= _state_0_call_0;
                            end
                        end
                    end
                    _state_1_call_0: begin
                        _gen0_circle_lines__ready <= 0;
                        _gen0_circle_lines__start <= 1;
                        _gen0_circle_lines_s_x <= _c_x1;
                        _gen0_circle_lines_s_y <= _c_y1;
                        _gen0_circle_lines_height <= _radius;
                        _state <= _state_0_call_0;
                        // $display("Calling %0d %0d %0d", _gen0_circle_lines__ready, _gen0_circle_lines__start, _gen0_circle_lines_s_x);
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
