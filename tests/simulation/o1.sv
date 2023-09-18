/*

# Python Function
        @verilogify(
            mode=Modes.OVERWRITE,
            namespace=ns,
        )
        def hrange(n):
            i = 0
            while i < n:
                yield i, i
                i += 1


# Test Cases
print(list(hrange(*(10,))))
print(list(hrange(*(10,))))

*/

module hrange (
    // Function parameters (only need to be set when start is high):
    input wire signed [31:0] n,

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
    typedef enum{_state_0_while_0,_state_1,_state_done,_state_idle} _state_t;
    _state_t _state;
    // Global variables
    reg signed [31:0] _i;
    reg signed [31:0] _n;
    // Core
    always @(posedge _clock) begin
        `ifdef DEBUG
        $display("hrange,%s,_start=%0d,_done=%0d,_ready=%0d,_valid=%0d,n=%0d,_n=%0d,_out0=%0d,_out1=%0d,_i=%0d", _state.name, _start, _done, _ready, _valid, n, _n, _out0, _out1, _i);
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
            _n <= n;
            _i <= $signed(0);
            if (($signed(0) < n)) begin
                _out0 <= $signed(0);
                _out1 <= $signed(0);
                _valid <= 1;
                _state <= _state_0_while_0;
            end else begin
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
                    _state_0_while_0: begin
                        _i <= $signed(_i + $signed(1));
                        if (($signed(_i + $signed(1)) < _n)) begin
                            _out0 <= $signed(_i + $signed(1));
                            _out1 <= $signed(_i + $signed(1));
                            _valid <= 1;
                            _state <= _state_0_while_0;
                        end else begin
                            if ($signed(!(_valid) && _ready)) begin
                                _done <= 1;
                                _state <= _state_idle;
                            end else begin
                                _state <= _state_done;
                            end
                        end
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
            mode=Modes.OVERWRITE,
            namespace=ns,
            optimization_level=1,
        )
        def dup_range_goal(n):
            inst = hrange(n)
            for i, j in inst:
                yield i


# Test Cases
print(list(dup_range_goal(*(10,))))

*/

module dup_range_goal (
    // Function parameters (only need to be set when start is high):
    input wire signed [31:0] n,

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
    typedef enum{_state_0_for_0,_state_1_call_0,_state_done,_state_idle} _state_t;
    _state_t _state;
    // Global variables
    reg signed [31:0] _i;
    reg signed [31:0] _j;
    reg signed [31:0] _n;
    // ================ Function Instance ================
    reg [31:0] _inst_hrange_n;
    wire [31:0] _inst_hrange_out0;
    wire [31:0] _inst_hrange_out1;
    wire _inst_hrange__valid;
    wire _inst_hrange__done;
    reg _inst_hrange__start;
    reg _inst_hrange__ready;
    hrange _inst (
        .n(_inst_hrange_n),
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
        $display("dup_range_goal,%s,_start=%0d,_done=%0d,_ready=%0d,_valid=%0d,n=%0d,_n=%0d,_out0=%0d,_i=%0d,_j=%0d", _state.name, _start, _done, _ready, _valid, n, _n, _out0, _i, _j);
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
            _n <= n;
            _inst_hrange__ready <= 0;
            _inst_hrange__start <= 1;
            _inst_hrange_n <= n;
            _state <= _state_0_for_0;
        end else begin
            // If ready or not valid, then continue computation
            if ((_ready || !(_valid))) begin
                case (_state)
                    _state_0_for_0: begin
                        _inst_hrange__ready <= 1;
                        _inst_hrange__start <= 0;
                        if ((1 && _inst_hrange__valid)) begin
                            _inst_hrange__ready <= 0;
                            _i <= _inst_hrange_out0;
                            _j <= _inst_hrange_out1;
                            if (_inst_hrange__done) begin
                                if ($signed(!(_valid) && _ready)) begin
                                    _done <= 1;
                                    _state <= _state_idle;
                                end else begin
                                    _state <= _state_done;
                                end
                            end else begin
                                _out0 <= _inst_hrange_out0;
                                _valid <= 1;
                                _state <= _state_0_for_8;
                            end
                        end else begin
                            if (_inst_hrange__done) begin
                                if ($signed(!(_valid) && _ready)) begin
                                    _done <= 1;
                                    _state <= _state_idle;
                                end else begin
                                    _state <= _state_done;
                                end
                            end else begin
                                _state <= _state_0_for_0;
                            end
                        end
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
