module generator(
    input wire _clock,
    input wire _start,
    input wire signed [31:0] a,
    input wire signed [31:0] b,
    input wire signed [31:0] c,
    input wire signed [31:0] d,
    output reg signed [31:0] _out0,
    output reg signed [31:0] _out1,
    output reg _done
);
    reg signed [31:0] _STATE;
    reg signed [31:0] _STATE_0;
    reg signed [31:0] _STATE_1;
    reg signed [31:0] _STATE_2;
        always @(posedge _clock) begin
            if (_start) begin
                _done <= 0;
                _STATE <= 0;
                _STATE_0 <= 0;
                _STATE_1 <= 1;
                _STATE_2 <= 2;
            end else begin
                case (_STATE) // STATEMENTS START
                    _STATE_0: begin
                        _out0 <= a;
                        _out1 <= b;
                        _STATE <= _STATE + 1; // INCREMENT STATE
                    end
                    _STATE_1: begin
                        _out0 <= c;
                        _out1 <= d;
                        _STATE <= _STATE + 1; // INCREMENT STATE
                    end
                    _STATE_2: begin // END STATEMENTS STATE
                        _done = 1;
                    end
                endcase // STATEMENTS END
            end
        end
endmodule
