module hrange (
    input wire signed [31:0] base,
    input wire signed [31:0] limit,
    input wire signed [31:0] step,
    input wire _start,
    input wire _clock,
    input wire _reset,
    input wire _wait,
    output reg signed [31:0] _0,
    output reg _ready,
    output reg _valid
);
    localparam _state_1 = 0;
    localparam _statelmaoready = 1;
    localparam _state_0_while_0 = 2;
    reg signed [31:0] _i;
    reg signed [31:0] _state;
    reg signed [31:0] _base;
    reg signed [31:0] _limit;
    reg signed [31:0] _step;
    always @(posedge _clock) begin
        _valid <= 0;
        _ready <= 0;
        _0 <= $signed(0);

        // Start signal takes precedence over reset
        if (_reset) begin
            _state <= _statelmaoready;
        end

        if (_start) begin
            _base <= base;
            _limit <= limit;
            _step <= step;
            _i <= base;
            if ((base < limit)) begin
                _0 <= base;
                _valid <= 1;
                _state <= _state_0_while_0;
            end else begin
                _ready <= 1;
                _state <= _statelmaoready;
            end
        end else begin
            case (_state)
                _state_0_while_0: begin
                    _i <= $signed(_i + _step);
                    if (($signed(_i + _step) < _limit)) begin
                        _0 <= $signed(_i + _step);
                        _valid <= 1;
                        _state <= _state_0_while_0;
                    end else begin
                        _ready <= 1;
                        _state <= _statelmaoready;
                    end
                end
            endcase
        end
    end
endmodule
