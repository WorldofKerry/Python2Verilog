/*

# Python Function
@verilogify(
    mode=Modes.OVERWRITE,
    module_output="./design/func_call/dup_range.sv",
    testbench_output="./design/func_call/dup_range_tb.sv",
    optimization_level=0,
)
def dup_range(base, limit, step):
    counter = base
    inst = 0  # fake generator
    while counter < limit:
        value = inst  # fake iter
        yield value
        yield value
        counter += step


# Test Cases
print(list(dup_range(*(0, 10, 2))))

*/

module dup_range (
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
    localparam _state_1 = 0;
    localparam _state_0_while = 1;
    localparam _state_0_while_3 = 2;
    localparam _state_fake = 3;
    localparam _state_0_while_0 = 4;
    localparam _state_0_while_2 = 5;
    localparam _state_2 = 6;
    localparam _state_0_while_1 = 7;
    // Global variables
    reg signed [31:0] _value;
    reg signed [31:0] _inst;
    reg signed [31:0] _counter;
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
            _counter <= base;
            _state <= _state_1;
        end else begin
            // If ready or not valid, then continue computation
            if ($signed(_ready || !(_valid))) begin
                case (_state)
                    _state_0_while_0: begin
                        _counter <= $signed(_counter + _step);
                        _state <= _state_0_while;
                    end
                    _state_0_while_1: begin
                        _0 <= _value;
                        _valid <= 1;
                        _state <= _state_0_while_0;
                    end
                    _state_0_while_2: begin
                        _0 <= _value;
                        _valid <= 1;
                        _state <= _state_0_while_1;
                    end
                    _state_0_while_3: begin
                        _value <= _inst;
                        _state <= _state_0_while_2;
                    end
                    _state_fake: begin
                        _done <= 1;
                        _state <= _state_fake;
                    end
                    _state_0_while: begin
                        if ((_counter < _limit)) begin
                            _state <= _state_0_while_3;
                        end else begin
                            _state <= _state_fake;
                        end
                    end
                    _state_1: begin
                        _inst <= $signed(0);
                        _state <= _state_0_while;
                    end
                endcase
            end
        end
    end
endmodule
