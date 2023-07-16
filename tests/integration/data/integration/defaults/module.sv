module defaults(
    input wire [31:0] a,
    input wire [31:0] b,
    input wire [31:0] c,
    input wire [31:0] d,
    input wire _start,
    input wire _clock,
    output reg [31:0] _out0,
    output reg [31:0] _out1,
    output reg _done,
    output reg _valid
);
    reg signed [31:0] _STATE;
    always @(posedge _clock) begin
    _valid <= 0;
        if (_start) begin
            _done <= 0;
            _STATE <= 0;
        end else begin
            case (_STATE)
                0: begin
                    _out0 <= a;
                    _out1 <= b;
                    _valid <= 1;
                    _STATE <= _STATE + 1;
                end
                1: begin
                    _out0 <= c;
                    _out1 <= d;
                    _valid <= 1;
                    _STATE <= _STATE + 1;
                    _done <= 1;
                end
            endcase
        end
    end
endmodule
