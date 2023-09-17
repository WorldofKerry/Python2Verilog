module circle_lines_tb (
);
    reg _clock;
    reg _start;
    reg _reset;
    reg _ready;
    reg signed [31:0] s_x;
    reg signed [31:0] s_y;
    reg signed [31:0] height;
    wire _done;
    wire _valid;
    wire signed [31:0] _out_0;
    wire signed [31:0] _out_1;
    wire signed [31:0] _out_2;
    wire signed [31:0] _out_3;
    wire signed [31:0] _out_4;
    wire signed [31:0] _out_5;
    circle_lines DUT (
        ._clock(_clock),
        ._start(_start),
        ._reset(_reset),
        ._ready(_ready),
        .s_x(s_x),
        .s_y(s_y),
        .height(height),
        ._done(_done),
        ._valid(_valid),
        ._out_0(_out_0),
        ._out_1(_out_1),
        ._out_2(_out_2),
        ._out_3(_out_3),
        ._out_4(_out_4),
        ._out_5(_out_5)
        );
    always #5 _clock = !_clock;
    initial begin
        _clock = 0;
        _start = 0;
        _ready = 1;
        _reset = 1;
        @(negedge _clock);
        _reset = 0;
        // ============ Test Case 0 with arguments (54, 52, 8) ============
        s_x = $signed(54);
        s_y = $signed(52);
        height = $signed(8);
        _start = 1;
        @(negedge _clock);
        s_x = 'x; // only need inputs when start is set
        s_y = 'x; // only need inputs when start is set
        height = 'x; // only need inputs when start is set
        _start = 0;
        while ((!(_done) || !(_ready))) begin
            // `if (_ready && _valid)` also works as a conditional
            if (_ready) begin
                $display("%0d, %0d, %0d, %0d, %0d, %0d, %0d, %0d", _valid, _ready, _out_0, _out_1, _out_2, _out_3, _out_4, _out_5);
            end
            @(negedge _clock);
        end
        if (_ready) begin
            $display("%0d, %0d, %0d, %0d, %0d, %0d, %0d, %0d", _valid, _ready, _out_0, _out_1, _out_2, _out_3, _out_4, _out_5);
        end
        $finish;
    end
endmodule
module triple_circle_tb (
);
    reg _clock;
    reg _start;
    reg _reset;
    reg _ready;
    reg signed [31:0] centre_x;
    reg signed [31:0] centre_y;
    reg signed [31:0] radius;
    wire _done;
    wire _valid;
    wire signed [31:0] _out_0;
    wire signed [31:0] _out_1;
    triple_circle DUT (
        ._clock(_clock),
        ._start(_start),
        ._reset(_reset),
        ._ready(_ready),
        .centre_x(centre_x),
        .centre_y(centre_y),
        .radius(radius),
        ._done(_done),
        ._valid(_valid),
        ._out_0(_out_0),
        ._out_1(_out_1)
        );
    always #5 _clock = !_clock;
    initial begin
        _clock = 0;
        _start = 0;
        _ready = 1;
        _reset = 1;
        @(negedge _clock);
        _reset = 0;
        // ============ Test Case 0 with arguments (50, 50, 8) ============
        centre_x = $signed(50);
        centre_y = $signed(50);
        radius = $signed(8);
        _start = 1;
        @(negedge _clock);
        centre_x = 'x; // only need inputs when start is set
        centre_y = 'x; // only need inputs when start is set
        radius = 'x; // only need inputs when start is set
        _start = 0;
        while ((!(_done) || !(_ready))) begin
            // `if (_ready && _valid)` also works as a conditional
            if (_ready) begin
                $display("%0d, %0d, %0d, %0d", _valid, _ready, _out_0, _out_1);
            end
            @(negedge _clock);
        end
        if (_ready) begin
            $display("%0d, %0d, %0d, %0d", _valid, _ready, _out_0, _out_1);
        end
        $finish;
    end
endmodule
