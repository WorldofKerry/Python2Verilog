module hrange_tb (
);
    reg _clock;
    reg _start;
    reg _reset;
    reg _ready;
    reg signed [31:0] n;
    wire _done;
    wire _valid;
    wire signed [31:0] _out0;
    wire signed [31:0] _out1;
    hrange DUT (
        ._clock(_clock),
        ._start(_start),
        ._reset(_reset),
        ._ready(_ready),
        .n(n),
        ._done(_done),
        ._valid(_valid),
        ._out0(_out0),
        ._out1(_out1)
        );
    always #5 _clock = !_clock;
    initial begin
        _clock = 0;
        _start = 0;
        _ready = 1;
        _reset = 1;
        @(negedge _clock);
        _reset = 0;
        // ============ Test Case 0 with arguments (10,) ============
        n = $signed(10);
        _start = 1;
        @(negedge _clock);
        n = 'x; // only need inputs when start is set
        _start = 0;
        while ((!(_done) || !(_ready))) begin
            // `if (_ready && _valid)` also works as a conditional
            if (_ready) begin
                $display("%0d, %0d, %0d, %0d", _valid, _ready, _out0, _out1);
            end
            @(negedge _clock);
        end
        if (_ready) begin
            $display("%0d, %0d, %0d, %0d", _valid, _ready, _out0, _out1);
        end
        // ============ Test Case 1 with arguments (10,) ============
        n = $signed(10);
        _start = 1;
        @(negedge _clock);
        n = 'x; // only need inputs when start is set
        _start = 0;
        while ((!(_done) || !(_ready))) begin
            // `if (_ready && _valid)` also works as a conditional
            if (_ready) begin
                $display("%0d, %0d, %0d, %0d", _valid, _ready, _out0, _out1);
            end
            @(negedge _clock);
        end
        if (_ready) begin
            $display("%0d, %0d, %0d, %0d", _valid, _ready, _out0, _out1);
        end
        $finish;
    end
endmodule
module dup_range_goal_tb (
);
    reg _clock;
    reg _start;
    reg _reset;
    reg _ready;
    reg signed [31:0] n;
    wire _done;
    wire _valid;
    wire signed [31:0] _out0;
    dup_range_goal DUT (
        ._clock(_clock),
        ._start(_start),
        ._reset(_reset),
        ._ready(_ready),
        .n(n),
        ._done(_done),
        ._valid(_valid),
        ._out0(_out0)
        );
    always #5 _clock = !_clock;
    initial begin
        _clock = 0;
        _start = 0;
        _ready = 1;
        _reset = 1;
        @(negedge _clock);
        _reset = 0;
        // ============ Test Case 0 with arguments (10,) ============
        n = $signed(10);
        _start = 1;
        @(negedge _clock);
        n = 'x; // only need inputs when start is set
        _start = 0;
        while ((!(_done) || !(_ready))) begin
            // `if (_ready && _valid)` also works as a conditional
            if (_ready) begin
                $display("%0d, %0d, %0d", _valid, _ready, _out0);
            end
            @(negedge _clock);
        end
        if (_ready) begin
            $display("%0d, %0d, %0d", _valid, _ready, _out0);
        end
        $finish;
    end
endmodule