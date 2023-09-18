/*

# Python Function
        @verilogify(
            mode=Modes.OVERWRITE,
            namespace=goal_namespace,
        )
        def hrange(base, limit, step):
            i = base
            while i < limit:
                yield i, i
                i += step


# Test Cases
print(list(hrange(*(1, 11, 3))))
print(list(hrange(*(0, 10, 2))))
print(list(hrange(*(0, 10, 2))))
print(list(hrange(*(0, 10, 2))))

*/

module hrange (
    // Function parameters (only need to be set when start is high):
    input wire signed [31:0] base,
    input wire signed [31:0] limit,
    input wire signed [31:0] step,

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
    typedef enum{_state_0_while_0,_state_1,_state_1_while,_state_done,_state_idle} _state_t;
    _state_t _state;
    // Global variables
    reg signed [31:0] _i;
    reg signed [31:0] _base;
    reg signed [31:0] _limit;
    reg signed [31:0] _step;
    // Core
    always @(posedge _clock) begin
        `ifdef DEBUG
        $display("hrange,%s,_start:%0d,_done:%0d,_ready:%0d,_valid:%0d,_reset:%0d,_clock:%0d,base:%0d,limit:%0d,step:%0d,_base:%0d,_limit:%0d,_step:%0d,_out0:%0d,_out1:%0d,_i%0d", _state.name, _start, _done, _ready, _valid, _reset, _clock, base, limit, step, _base, _limit, _step, _out0, _out1, _i);
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
            _base <= base;
            _limit <= limit;
            _step <= step;
            if ((_i < limit)) begin
                _i <= $signed(_i + step);
                _out0 <= $signed(_i + step);
                _out1 <= $signed(_i + step);
                _valid <= 1;
                _state <= _state_1_while;
            end else begin
                _i <= base;
                if ($signed(!(_valid) && _ready)) begin
                    _done <= 1;
                    _state <= _state_idle;
                end else begin
                    _state <= _state_done;
                end
            end
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
                endcase
            end
        end
    end
endmodule
/*

# Python Function
        @verilogify(
            mode=Modes.OVERWRITE,
            namespace=goal_namespace,
            optimization_level=0,
        )
        def dup_range_goal(base, limit, step):
            inst = hrange(base, limit, step)
            for i, j in inst:
                if i > 4:
                    yield i
                yield j


# Test Cases
print(list(dup_range_goal(*(0, 10, 2))))

*/

module dup_range_goal (
    // Function parameters (only need to be set when start is high):
    input wire signed [31:0] base,
    input wire signed [31:0] limit,
    input wire signed [31:0] step,

    input wire _clock, // clock for sync
    input wire _reset, // set high to reset, i.e. done will be high
    input wire _start, // set high to capture inputs (in same cycle) and start generating

    // Implements a ready/valid handshake based on
    // http://www.cjdrake.com/readyvalid-protocol-primer.html
    input wire _ready, // set high when caller is ready for output
    output reg _valid, // is high if output values are valid

    output reg _done, // is high if module done outputting

    // Output values as a tuple with respective index(es)
    output reg signed [31:0] _out0
);
    // State variables
    typedef enum{_state_0_call_0,_state_0_for_0,_state_0_for_body_0,_state_0_for_body_1,_state_0_for_body_1_t_0,_state_1_call_0,_state_1_for_0,_state_1_for_body_0,_state_1_for_body_0_t_0,_state_1_for_body_1,_state_done,_state_idle} _state_t;
    _state_t _state;
    // Global variables
    reg signed [31:0] _i;
    reg signed [31:0] _j;
    reg signed [31:0] _base;
    reg signed [31:0] _limit;
    reg signed [31:0] _step;
    // ================ Function Instance ================
    reg [31:0] _inst_hrange_base;
    reg [31:0] _inst_hrange_limit;
    reg [31:0] _inst_hrange_step;
    wire [31:0] _inst_hrange_out0;
    wire [31:0] _inst_hrange_out1;
    wire _inst_hrange__valid;
    wire _inst_hrange__done;
    reg _inst_hrange__start;
    reg _inst_hrange__ready;
    hrange _inst (
        .base(_inst_hrange_base),
        .limit(_inst_hrange_limit),
        .step(_inst_hrange_step),
        ._out0(_inst_hrange_out0),
        ._out1(_inst_hrange_out1),
        ._valid(_inst_hrange__valid),
        ._done(_inst_hrange__done),
        ._clock(_clock),
        ._start(_inst_hrange__start),
        ._reset(_reset),
        ._ready(_inst_hrange__ready)
        );
    // Core
    always @(posedge _clock) begin
        `ifdef DEBUG
        $display("dup_range_goal,%s,_start:%0d,_done:%0d,_ready:%0d,_valid:%0d,_reset:%0d,_clock:%0d,base:%0d,limit:%0d,step:%0d,_base:%0d,_limit:%0d,_step:%0d,_out0:%0d,_i:%0d,_j%0d", _state.name, _start, _done, _ready, _valid, _reset, _clock, base, limit, step, _base, _limit, _step, _out0, _i, _j);
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
            _base <= base;
            _limit <= limit;
            _step <= step;
            _state <= _state_1_call_0;
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
                    _state_0_for_body_0: begin
                        _out0 <= _j;
                        _valid <= 1;
                        _state <= _state_0_for_0;
                    end
                    _state_0_for_body_1_t_0: begin
                        _out0 <= _i;
                        _valid <= 1;
                        _state <= _state_0_for_body_0;
                    end
                    _state_0_for_body_1: begin
                        if ($signed(_i > $signed(4))) begin
                            _state <= _state_0_for_body_1_t_0;
                        end else begin
                            _state <= _state_0_for_body_0;
                        end
                    end
                    _state_0_for_0: begin
                        _inst_hrange__ready <= 1;
                        _inst_hrange__start <= 0;
                        if ((_inst_hrange__ready && _inst_hrange__valid)) begin
                            _inst_hrange__ready <= 0;
                            _i <= _inst_hrange_out0;
                            _j <= _inst_hrange_out1;
                            if (_inst_hrange__done) begin
                                _state <= _state_done;
                            end else begin
                                _state <= _state_0_for_body_1;
                            end
                        end else begin
                            if (_inst_hrange__done) begin
                                _state <= _state_done;
                            end else begin
                                _state <= _state_0_for_0;
                            end
                        end
                    end
                    _state_1_call_0: begin
                        _inst_hrange__ready <= 0;
                        _inst_hrange__start <= 1;
                        _inst_hrange_base <= _base;
                        _inst_hrange_limit <= _limit;
                        _inst_hrange_step <= _step;
                        _state <= _state_0_for_0;
                    end
                endcase
            end
        end
    end
endmodule