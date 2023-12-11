module multiplier_generator (
    input logic [31:0] multiplier,
    input logic [31:0] multiplicand,
    input logic __ready,
    input logic __start,
    input logic __clock,
    input logic __reset,
    output logic __valid,
    output logic __done,
    output logic [31:0] __output_0
);
    localparam __state_0 = 0;
    localparam __state_1 = 1;
    localparam __state_start = 2;
    localparam __state_done = 3;
    logic [31:0] mem_0;
    logic [31:0] mem_1;
    logic [31:0] mem_2;
    logic [31:0] mem_3;
    logic [31:0] __state;
    always @(posedge __clock) begin
        $display("state %0d, reset %0d, start %0d, ready %0d, valid %0d, done %0d, mem_0 %0d, mem_2 %0d, multiplier %0d, multiplicand %0d", __state, __reset, __start, __ready, __valid, __done, mem_0, mem_2, multiplier, multiplicand);
        if (__ready) begin
            __valid <= 0;
            __done <= 0;
        end
        // Start signal takes precedence over reset
        if ((__reset)) begin
            __done <= 0;
            __valid <= 0;
            __state <= 123;
        end
        if (__start) begin
            __done <= 0;
            __valid <= 0;
            mem_0 <= multiplier;
            mem_1 <= multiplicand;
            __state <= __state_0;
        end else begin
            // If ready or not valid, then continue computation
            if ((__ready || !(__valid))) begin
                case (__state)
                    __state_done : begin
                        __done <= 1;
                        __valid <= 1;
                        __state <= __state <= 123;
                    end
                    __state_0 : begin
                        if((0 < mem_0)) begin
                            mem_0 <= (0 + 1);
                            mem_1 <= (0 + mem_1);
                            mem_2 <= mem_0;
                            mem_3 <= mem_1;
                            __state <= __state_1;
                        end else begin
                            __valid <= 1;
                            __output_0 <= 0;
                            __state <= __state_done;
                        end
                    end
                    __state_1 : begin
                        if((mem_0 < mem_2)) begin
                            mem_0 <= (mem_0 + 1);
                            mem_1 <= (mem_1 + mem_3);
                            mem_2 <= mem_2;
                            mem_3 <= mem_3;
                            __state <= __state_1;
                        end else begin
                            __valid <= 1;
                            __output_0 <= mem_1;
                            __state <= __state_done;
                        end
                    end
                endcase
            end
        end
    end
endmodule
module quad_multiply (
    // Function parameters (only need to be set when start is high):
    input wire signed [31:0] left,
    input wire signed [31:0] right,

    input wire __clock, // clock for sync
    input wire __reset, // set high to reset, i.e. done will be high
    input wire __start, // set high to capture inputs (in same cycle) and start generating

    // Implements the ready/valid handshake
    input wire __ready, // set high when caller is ready for output
    output reg __valid, // is high if output values are valid

    output reg __done, // is high if module done outputting

    // Output values as a tuple with respective index(es)
    output reg signed [31:0] __output_0
);
    // State variables
    typedef enum{_state0,_state2_for_0,_state2_for_1,_state3_call_0,_state4_for_0,_state4_for_1,_state5_call_0,_state6_for_0,_state6_for_1,_state7_for_0,_state7_for_1,_state_done,_state_idle} _state_t;
    _state_t _state;
    // Local variables
    reg signed [31:0] _val;
    reg signed [31:0] _left;
    reg signed [31:0] _right;
    // ================ Function Instance ================
    reg [31:0] _inst_multiplier_generator_multiplicand;
    reg [31:0] _inst_multiplier_generator_multiplier;
    wire [31:0] _inst_multiplier_generator__output_0;
    wire __multiplier_generator_inst__valid;
    wire __multiplier_generator_inst__done;
    reg __multiplier_generator_inst__start;
    reg __multiplier_generator_inst__ready;
    multiplier_generator _inst (
        .multiplicand(_inst_multiplier_generator_multiplicand),
        .multiplier(_inst_multiplier_generator_multiplier),
        .__output_0(_inst_multiplier_generator__output_0),
        .__valid(__multiplier_generator_inst__valid),
        .__done(__multiplier_generator_inst__done),
        .__clock(__clock),
        .__start(__multiplier_generator_inst__start),
        .__reset(__reset),
        .__ready(__multiplier_generator_inst__ready)
        );
    // ================ Function Instance ================
    reg [31:0] _nested4_multiplier_generator_multiplicand;
    reg [31:0] _nested4_multiplier_generator_multiplier;
    wire [31:0] _nested4_multiplier_generator__output_0;
    wire __multiplier_generator_nested4__valid;
    wire __multiplier_generator_nested4__done;
    reg __multiplier_generator_nested4__start;
    reg __multiplier_generator_nested4__ready;
    multiplier_generator _nested4 (
        .multiplicand(_nested4_multiplier_generator_multiplicand),
        .multiplier(_nested4_multiplier_generator_multiplier),
        .__output_0(_nested4_multiplier_generator__output_0),
        .__valid(__multiplier_generator_nested4__valid),
        .__done(__multiplier_generator_nested4__done),
        .__clock(__clock),
        .__start(__multiplier_generator_nested4__start),
        .__reset(__reset),
        .__ready(__multiplier_generator_nested4__ready)
        );
    // Core
    always @(posedge __clock) begin
        // `ifdef DEBUG
        $display("quad_multiply,%s,__start=%0d,__done=%0d,__ready=%0d,__valid=%0d,left=%0d,right=%0d,_left=%0d,_right=%0d,__output_0=%0d,_val=%0d", _state.name, __start, __done, __ready, __valid, left, right, _left, _right, __output_0, _val);
        // `endif
        __multiplier_generator_inst__ready <= 0;
        __multiplier_generator_inst__start <= 0;
        __multiplier_generator_nested4__ready <= 0;
        __multiplier_generator_nested4__start <= 0;
        if (__ready) begin
            __valid <= 0;
            __done <= 0;
        end
        // Start signal takes precedence over reset
        if ((__reset || __start)) begin
            _state <= _state_idle;
            __done <= 0;
            __valid <= 0;
        end
        if (__start) begin
            _left <= left;
            _right <= right;
            _state <= _state;
            __multiplier_generator_inst__ready <= 0;
            __multiplier_generator_inst__start <= 1;
            _inst_multiplier_generator_multiplicand <= left;
            _inst_multiplier_generator_multiplier <= right;
            _state <= _state2_for_0;
        end else begin
            // If ready or not valid, then continue computation
            if ((__ready || !(__valid))) begin
                case (_state)
                    _state2_for_0: begin
                        if ((__multiplier_generator_inst__ready && __multiplier_generator_inst__valid)) begin
                            __multiplier_generator_inst__ready <= 0;
                            if (__multiplier_generator_inst__done) begin
                                _state <= _state3_call_0;
                            end else begin
                                _val <= _inst_multiplier_generator__output_0;
                                __output_0 <= _inst_multiplier_generator__output_0;
                                __valid <= 1;
                                _state <= _state2_for_0;
                            end
                        end else begin
                            if ((__ready || !(__valid))) begin
                                __multiplier_generator_inst__ready <= 1;
                                _state <= _state2_for_0;
                            end else begin
                                if ((__multiplier_generator_inst__ready && __multiplier_generator_inst__valid)) begin
                                    __multiplier_generator_inst__ready <= 0;
                                    if (__multiplier_generator_inst__done) begin
                                        _state <= _state3_call_0;
                                    end else begin
                                        _val <= _inst_multiplier_generator__output_0;
                                        __output_0 <= _inst_multiplier_generator__output_0;
                                        __valid <= 1;
                                        _state <= _state2_for_0;
                                    end
                                end else begin
                                    _state <= _state2_for_1;
                                end
                            end
                        end
                    end
                    _state2_for_1: begin
                        if ((__ready || !(__valid))) begin
                            __multiplier_generator_inst__ready <= 1;
                            _state <= _state2_for_0;
                        end else begin
                            if ((__multiplier_generator_inst__ready && __multiplier_generator_inst__valid)) begin
                                __multiplier_generator_inst__ready <= 0;
                                if (__multiplier_generator_inst__done) begin
                                    _state <= _state3_call_0;
                                end else begin
                                    _val <= _inst_multiplier_generator__output_0;
                                    __output_0 <= _inst_multiplier_generator__output_0;
                                    __valid <= 1;
                                    _state <= _state2_for_0;
                                end
                            end else begin
                                if ((__ready || !(__valid))) begin
                                    __multiplier_generator_inst__ready <= 1;
                                    _state <= _state2_for_0;
                                end else begin
                                    _state <= _state2_for_0;
                                end
                            end
                        end
                    end
                    _state3_call_0: begin
                        __multiplier_generator_inst__ready <= 0;
                        __multiplier_generator_inst__start <= 1;
                        _inst_multiplier_generator_multiplicand <= _left;
                        _inst_multiplier_generator_multiplier <= -(_right);
                        _state <= _state4_for_0;
                    end
                    _state4_for_0: begin
                        if ((__multiplier_generator_inst__ready && __multiplier_generator_inst__valid)) begin
                            __multiplier_generator_inst__ready <= 0;
                            if (__multiplier_generator_inst__done) begin
                                _state <= _state5_call_0;
                            end else begin
                                _val <= _inst_multiplier_generator__output_0;
                                __output_0 <= _inst_multiplier_generator__output_0;
                                __valid <= 1;
                                _state <= _state4_for_0;
                            end
                        end else begin
                            if ((__ready || !(__valid))) begin
                                __multiplier_generator_inst__ready <= 1;
                                _state <= _state4_for_0;
                            end else begin
                                if ((__multiplier_generator_inst__ready && __multiplier_generator_inst__valid)) begin
                                    __multiplier_generator_inst__ready <= 0;
                                    if (__multiplier_generator_inst__done) begin
                                        _state <= _state5_call_0;
                                    end else begin
                                        _val <= _inst_multiplier_generator__output_0;
                                        __output_0 <= _inst_multiplier_generator__output_0;
                                        __valid <= 1;
                                        _state <= _state4_for_0;
                                    end
                                end else begin
                                    _state <= _state4_for_1;
                                end
                            end
                        end
                    end
                    _state4_for_1: begin
                        if ((__ready || !(__valid))) begin
                            __multiplier_generator_inst__ready <= 1;
                            _state <= _state4_for_0;
                        end else begin
                            if ((__multiplier_generator_inst__ready && __multiplier_generator_inst__valid)) begin
                                __multiplier_generator_inst__ready <= 0;
                                if (__multiplier_generator_inst__done) begin
                                    _state <= _state5_call_0;
                                end else begin
                                    _val <= _inst_multiplier_generator__output_0;
                                    __output_0 <= _inst_multiplier_generator__output_0;
                                    __valid <= 1;
                                    _state <= _state4_for_0;
                                end
                            end else begin
                                if ((__ready || !(__valid))) begin
                                    __multiplier_generator_inst__ready <= 1;
                                    _state <= _state4_for_0;
                                end else begin
                                    _state <= _state4_for_0;
                                end
                            end
                        end
                    end
                    _state5_call_0: begin
                        __multiplier_generator_inst__ready <= 0;
                        __multiplier_generator_inst__start <= 1;
                        _inst_multiplier_generator_multiplicand <= -(_left);
                        _inst_multiplier_generator_multiplier <= _right;
                        _state <= _state6_for_0;
                    end
                    _state6_for_0: begin
                        if ((__multiplier_generator_inst__ready && __multiplier_generator_inst__valid)) begin
                            __multiplier_generator_inst__ready <= 0;
                            if (__multiplier_generator_inst__done) begin
                                __multiplier_generator_nested4__ready <= 0;
                                __multiplier_generator_nested4__start <= 1;
                                _nested4_multiplier_generator_multiplicand <= -(_left);
                                _nested4_multiplier_generator_multiplier <= -(_right);
                                _state <= _state7_for_0;
                            end else begin
                                _val <= _inst_multiplier_generator__output_0;
                                __output_0 <= _inst_multiplier_generator__output_0;
                                __valid <= 1;
                                _state <= _state6_for_0;
                            end
                        end else begin
                            if ((__ready || !(__valid))) begin
                                __multiplier_generator_inst__ready <= 1;
                                _state <= _state6_for_0;
                            end else begin
                                if ((__multiplier_generator_inst__ready && __multiplier_generator_inst__valid)) begin
                                    __multiplier_generator_inst__ready <= 0;
                                    if (__multiplier_generator_inst__done) begin
                                        __multiplier_generator_nested4__ready <= 0;
                                        __multiplier_generator_nested4__start <= 1;
                                        _nested4_multiplier_generator_multiplicand <= -(_left);
                                        _nested4_multiplier_generator_multiplier <= -(_right);
                                        _state <= _state7_for_0;
                                    end else begin
                                        _val <= _inst_multiplier_generator__output_0;
                                        __output_0 <= _inst_multiplier_generator__output_0;
                                        __valid <= 1;
                                        _state <= _state6_for_0;
                                    end
                                end else begin
                                    _state <= _state6_for_1;
                                end
                            end
                        end
                    end
                    _state6_for_1: begin
                        if ((__ready || !(__valid))) begin
                            __multiplier_generator_inst__ready <= 1;
                            _state <= _state6_for_0;
                        end else begin
                            if ((__multiplier_generator_inst__ready && __multiplier_generator_inst__valid)) begin
                                __multiplier_generator_inst__ready <= 0;
                                if (__multiplier_generator_inst__done) begin
                                    __multiplier_generator_nested4__ready <= 0;
                                    __multiplier_generator_nested4__start <= 1;
                                    _nested4_multiplier_generator_multiplicand <= -(_left);
                                    _nested4_multiplier_generator_multiplier <= -(_right);
                                    _state <= _state7_for_0;
                                end else begin
                                    _val <= _inst_multiplier_generator__output_0;
                                    __output_0 <= _inst_multiplier_generator__output_0;
                                    __valid <= 1;
                                    _state <= _state6_for_0;
                                end
                            end else begin
                                if ((__ready || !(__valid))) begin
                                    __multiplier_generator_inst__ready <= 1;
                                    _state <= _state6_for_0;
                                end else begin
                                    _state <= _state6_for_0;
                                end
                            end
                        end
                    end
                    _state7_for_0: begin
                        if ((__multiplier_generator_nested4__ready && __multiplier_generator_nested4__valid)) begin
                            __multiplier_generator_nested4__ready <= 0;
                            if (__multiplier_generator_nested4__done) begin
                                __done <= 1;
                                __valid <= 1;
                                _state <= _state_idle;
                            end else begin
                                _val <= _nested4_multiplier_generator__output_0;
                                __output_0 <= _nested4_multiplier_generator__output_0;
                                __valid <= 1;
                                _state <= _state7_for_0;
                            end
                        end else begin
                            if ((__ready || !(__valid))) begin
                                __multiplier_generator_nested4__ready <= 1;
                                _state <= _state7_for_0;
                            end else begin
                                if ((__multiplier_generator_nested4__ready && __multiplier_generator_nested4__valid)) begin
                                    __multiplier_generator_nested4__ready <= 0;
                                    if (__multiplier_generator_nested4__done) begin
                                        __done <= 1;
                                        __valid <= 1;
                                        _state <= _state_idle;
                                    end else begin
                                        _val <= _nested4_multiplier_generator__output_0;
                                        __output_0 <= _nested4_multiplier_generator__output_0;
                                        __valid <= 1;
                                        _state <= _state7_for_0;
                                    end
                                end else begin
                                    _state <= _state7_for_1;
                                end
                            end
                        end
                    end
                    _state7_for_1: begin
                        if ((__ready || !(__valid))) begin
                            __multiplier_generator_nested4__ready <= 1;
                            _state <= _state7_for_0;
                        end else begin
                            if ((__multiplier_generator_nested4__ready && __multiplier_generator_nested4__valid)) begin
                                __multiplier_generator_nested4__ready <= 0;
                                if (__multiplier_generator_nested4__done) begin
                                    __done <= 1;
                                    __valid <= 1;
                                    _state <= _state_idle;
                                end else begin
                                    _val <= _nested4_multiplier_generator__output_0;
                                    __output_0 <= _nested4_multiplier_generator__output_0;
                                    __valid <= 1;
                                    _state <= _state7_for_0;
                                end
                            end else begin
                                if ((__ready || !(__valid))) begin
                                    __multiplier_generator_nested4__ready <= 1;
                                    _state <= _state7_for_0;
                                end else begin
                                    _state <= _state7_for_0;
                                end
                            end
                        end
                    end
                endcase
            end
        end
    end
endmodule
