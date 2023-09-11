/*

# Python Function
@verilogify(mode=Modes.OVERWRITE)
def hrange(base, limit, step):
    i = base
    while i < limit:
        yield i
        i += step


# Test Cases
print(list(hrange(*(0, 10, 2))))
print(list(hrange(*(0, 10, 2))))
print(list(hrange(*(0, 10, 2))))

*/

module hrange (
    // Function parameters:
    input wire signed [31:0] base,
    input wire signed [31:0] limit,
    input wire signed [31:0] step,

    input wire _clock, // clock for sync
    input wire _reset, // set high to reset, i.e. done will be high
    input wire _start, // set high to capture inputs (in same cycle) and start generating

    // Implements a ready/valid handshake based on
    // http://www.cjdrake.com/readyvalid-protocol-primer.html
    input wire _ready, // set high when caller is ready for output
    output reg _valid, // is high if output is valid

    output reg _done, // is high if module done outputting

    // Output values as a tuple with respective index(es)
    output reg signed [31:0] _0
);
    localparam _state_0_while_0 = 0;
    localparam _state_1 = 1;
    localparam _state_fake = 2;
    // Global variables
    reg signed [31:0] _i;
    reg signed [31:0] _state;
    reg signed [31:0] _base;
    reg signed [31:0] _limit;
    reg signed [31:0] _step;
    always @(posedge _clock) begin
        _done <= 0;
        if (_ready) begin
            _valid <= 0;
        end
        // Start signal takes precedence over reset
        if (_reset) begin
            _state <= _state_fake;
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
                _done <= 1;
                _state <= _state_fake;
            end
        end else begin
            // If ready or not valid, then continue computation
            if ($signed(_ready || !(_valid))) begin
                case (_state)
                    _state_0_while_0: begin
                        _i <= $signed(_i + _step);
                        if (($signed(_i + _step) < _limit)) begin
                            _0 <= $signed(_i + _step);
                            _valid <= 1;
                            _state <= _state_0_while_0;
                        end else begin
                            _done <= 1;
                            _state <= _state_fake;
                        end
                    end
                endcase
            end
        end
    end
endmodule
