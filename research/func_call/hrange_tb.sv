module hrange_tb (
);
    reg _clock;
    reg _start;
    reg _reset;
    wire signed [31:0] _0;
    reg signed [31:0] base;
    reg signed [31:0] limit;
    reg signed [31:0] step;
    wire _ready;
    wire _valid;
    hrange DUT (
        ._clock(_clock),
        ._start(_start),
        ._reset(_reset),
        ._0(_0),
        .base(base),
        .limit(limit),
        .step(step),
        ._ready(_ready),
        ._valid(_valid)
        );
    always #5 _clock = !_clock;
    initial begin
        _clock = 0;
        _start = 0;
        _reset = 1;
        @(negedge _clock);
        _reset = 0;

        // ============ Test Case 0 with arguments (0, 10, 2) ============
        base = $signed(0);
        limit = $signed(10);
        step = $signed(2);
        _start = 1;

        @(negedge _clock);
        base = 'x; // only need inputs at start
        limit = 'x; // only need inputs at start
        step = 'x; // only need inputs at start
        _start = 0;

        while (!(_ready)) begin
            $display("%0d, %0d", _valid, _0);
            @(negedge _clock);
        end
        $display("%0d, %0d", _valid, _0);

        $finish;
    end
endmodule
