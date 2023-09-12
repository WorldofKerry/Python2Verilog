/*

# Python Function
@verilogify(
    mode=Modes.OVERWRITE,
    module_output="./design/func_call/dup_range_goal.sv",
    testbench_output="./design/func_call/dup_range_goal_tb.sv",
    optimization_level=1,
)
def dup_range_goal(base, limit, step):
    inst = hrange(base, limit, step)
    for i, j in inst:
        yield i
        yield j


# Test Cases
print(list(dup_range_goal(*(0, 10, 2))))

*/

module dup_range_goal (
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
    localparam _state_0_call_0 = 0;
    localparam _state_0_for_0 = 1;
    localparam _state_0_for_1 = 2;
    localparam _state_1_call_0 = 3;
    localparam _state_done = 4;
    // Global variables
    reg signed [31:0] _i;
    reg signed [31:0] _j;
    reg signed [31:0] _state;
    reg signed [31:0] _base;
    reg signed [31:0] _limit;
    reg signed [31:0] _step;
    // ================ Function Instance ================
    hrange _inst (
        .base(_inst_hrange_base),
        .limit(_inst_hrange_limit),
        .step(_inst_hrange_step),
        ._0(_inst_hrange_0),
        ._1(_inst_hrange_1),
        ._valid(_inst_hrange__valid),
        ._done(_inst_hrange__done),
        ._clock(_clock),
        ._start(_inst_hrange__start),
        ._reset(_inst_hrange__reset),
        ._ready(_inst_hrange__ready)
        );
    reg [31:0] _inst_hrange_base;
    reg [31:0] _inst_hrange_limit;
    reg [31:0] _inst_hrange_step;
    wire [31:0] _inst_hrange_0;
    wire [31:0] _inst_hrange_1;
    wire _inst_hrange__valid;
    wire _inst_hrange__done;
    reg _inst_hrange__start;
    reg _inst_hrange__ready;
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
            _base <= base;
            _limit <= limit;
            _step <= step;
            _inst_hrange__ready <= 0;
            _inst_hrange__start <= 1;
            _inst_hrange_base <= base;
            _inst_hrange_limit <= limit;
            _inst_hrange_step <= step;
            _state <= _state_0_call_0;
        end else begin
            // If ready or not valid, then continue computation
            if ((_ready || !(_valid))) begin
                case (_state)
                    _state_done: begin
                        _done <= 1;
                        _state <= _state_done;
                    end
                    _state_0_for_0: begin
                        _0 <= _j;
                        _valid <= 1;
                        _state <= _state_0_call_0;
                    end
                    _state_0_for_1: begin
                        _0 <= _i;
                        _valid <= 1;
                        _state <= _state_0_for_0;
                    end
                    _state_0_call_0: begin
                        _inst_hrange__ready <= 1;
                        _inst_hrange__start <= 0;
                        if ((_inst_hrange__ready && _inst_hrange__valid)) begin
                            _inst_hrange__ready <= 0;
                            _i <= _inst_hrange_0;
                            _j <= _inst_hrange_1;
                            if (_inst_hrange__done) begin
                                _state <= _state_done;
                            end else begin
                                _state <= _state_0_for_1;
                            end
                        end else begin
                            if (_inst_hrange__done) begin
                                _state <= _state_done;
                            end else begin
                                _state <= _state_0_call_0;
                            end
                        end
                    end
                endcase
            end
        end
    end
endmodule
