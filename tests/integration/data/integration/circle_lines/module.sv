module circle_lines(
    input wire [31:0] s_x,
    input wire [31:0] s_y,
    input wire [31:0] height,
    input wire _start,
    input wire _clock,
    output reg [31:0] _out0,
    output reg [31:0] _out1,
    output reg _done,
    output reg _valid
);
    reg signed [31:0] _STATE;
    reg signed [31:0] x;
    reg signed [31:0] y;
    reg signed [31:0] d;
    reg signed [31:0] _WHILE;
    reg signed [31:0] _WHILE1_STATE;
    reg signed [31:0] _WHILE1_IF;
    reg signed [31:0] _WHILE1_IF2_STATE;
    reg signed [31:0] _WHILE1_IF3_STATE;
    reg signed [31:0] _WHILE1_IF4_STATE;
    reg signed [31:0] _WHILE1_IF5_STATE;
    reg signed [31:0] _WHILE6_STATE;
    reg signed [31:0] _WHILE6_IF;
    reg signed [31:0] _WHILE6_IF7_STATE;
    reg signed [31:0] _WHILE6_IF8_STATE;
    reg signed [31:0] _WHILE6_IF9_STATE;
    reg signed [31:0] _WHILE6_IF10_STATE;
    always @(posedge _clock) begin
    _valid <= 0;
        if (_start) begin
            _done <= 0;
            _STATE <= 0;
            x <= 0;
            y <= 0;
            d <= 0;
            _WHILE <= 0;
            _WHILE1_STATE <= 0;
            _WHILE1_IF <= 0;
            _WHILE1_IF2_STATE <= 0;
            _WHILE1_IF3_STATE <= 0;
            _WHILE1_IF4_STATE <= 0;
            _WHILE1_IF5_STATE <= 0;
            _WHILE6_STATE <= 0;
            _WHILE6_IF <= 0;
            _WHILE6_IF7_STATE <= 0;
            _WHILE6_IF8_STATE <= 0;
            _WHILE6_IF9_STATE <= 0;
            _WHILE6_IF10_STATE <= 0;
        end else begin
            case (_STATE)
                0: begin
                    x <= 0;
                    _STATE <= _STATE + 1;
                end
                1: begin
                    y <= height;
                    _STATE <= _STATE + 1;
                end
                2: begin
                    d <= (3 - (2 * height));
                    _STATE <= _STATE + 1;
                end
                3: begin
                    _out0 <= (s_x + x);
                    _out1 <= (s_y + y);
                    _valid <= 1;
                    _STATE <= _STATE + 1;
                end
                4: begin
                    _out0 <= (s_x + x);
                    _out1 <= (s_y - y);
                    _valid <= 1;
                    _STATE <= _STATE + 1;
                end
                5: begin
                    _out0 <= (s_x - x);
                    _out1 <= (s_y + y);
                    _valid <= 1;
                    _STATE <= _STATE + 1;
                end
                6: begin
                    _out0 <= (s_x - x);
                    _out1 <= (s_y - y);
                    _valid <= 1;
                    _STATE <= _STATE + 1;
                end
                7: begin
                    _out0 <= (s_x + y);
                    _out1 <= (s_y + x);
                    _valid <= 1;
                    _STATE <= _STATE + 1;
                end
                8: begin
                    _out0 <= (s_x + y);
                    _out1 <= (s_y - x);
                    _valid <= 1;
                    _STATE <= _STATE + 1;
                end
                9: begin
                    _out0 <= (s_x - y);
                    _out1 <= (s_y + x);
                    _valid <= 1;
                    _STATE <= _STATE + 1;
                end
                10: begin
                    _out0 <= (s_x - y);
                    _out1 <= (s_y - x);
                    _valid <= 1;
                    _STATE <= _STATE + 1;
                end
                11: begin
                    case (_WHILE)
                        0: begin
                            if (!(y >= x)) begin     _STATE <= _STATE + 1;     _done <= 1; end else begin     _WHILE <= 1; end
                        end
                        1: begin
                            case (_WHILE6_STATE)
                                0: begin
                                    x <= (x + 1);
                                    _WHILE6_STATE <= _WHILE6_STATE + 1;
                                end
                                1: begin
                                    case (_WHILE6_IF)
                                        0: begin
                                            if (d > 0)
                                            _WHILE6_IF <= 1;
                                            else _WHILE6_IF <= 2;
                                        end
                                        1: begin
                                            case (_WHILE6_IF9_STATE)
                                                0: begin
                                                    y <= (y - 1);
                                                    _WHILE6_IF9_STATE <= _WHILE6_IF9_STATE + 1;
                                                end
                                                1: begin
                                                    d <= ((d + (4 * (x - y))) + 10);
                                                    _WHILE6_IF9_STATE <= _WHILE6_IF9_STATE + 1;
                                                    _WHILE6_STATE <= _WHILE6_STATE + 1;
                                                    _WHILE6_IF <= 0;
                                                    _WHILE6_IF9_STATE <= 0;
                                                end
                                            endcase
                                        end
                                        2: begin
                                            case (_WHILE6_IF10_STATE)
                                                0: begin
                                                    d <= ((d + (4 * x)) + 6);
                                                    _WHILE6_IF10_STATE <= _WHILE6_IF10_STATE + 1;
                                                    _WHILE6_STATE <= _WHILE6_STATE + 1;
                                                    _WHILE6_IF <= 0;
                                                    _WHILE6_IF10_STATE <= 0;
                                                end
                                            endcase
                                        end
                                    endcase
                                end
                                2: begin
                                    _out0 <= (s_x + x);
                                    _out1 <= (s_y + y);
                                    _valid <= 1;
                                    _WHILE6_STATE <= _WHILE6_STATE + 1;
                                end
                                3: begin
                                    _out0 <= (s_x + x);
                                    _out1 <= (s_y - y);
                                    _valid <= 1;
                                    _WHILE6_STATE <= _WHILE6_STATE + 1;
                                end
                                4: begin
                                    _out0 <= (s_x - x);
                                    _out1 <= (s_y + y);
                                    _valid <= 1;
                                    _WHILE6_STATE <= _WHILE6_STATE + 1;
                                end
                                5: begin
                                    _out0 <= (s_x - x);
                                    _out1 <= (s_y - y);
                                    _valid <= 1;
                                    _WHILE6_STATE <= _WHILE6_STATE + 1;
                                end
                                6: begin
                                    _out0 <= (s_x + y);
                                    _out1 <= (s_y + x);
                                    _valid <= 1;
                                    _WHILE6_STATE <= _WHILE6_STATE + 1;
                                end
                                7: begin
                                    _out0 <= (s_x + y);
                                    _out1 <= (s_y - x);
                                    _valid <= 1;
                                    _WHILE6_STATE <= _WHILE6_STATE + 1;
                                end
                                8: begin
                                    _out0 <= (s_x - y);
                                    _out1 <= (s_y + x);
                                    _valid <= 1;
                                    _WHILE6_STATE <= _WHILE6_STATE + 1;
                                end
                                9: begin
                                    _out0 <= (s_x - y);
                                    _out1 <= (s_y - x);
                                    _valid <= 1;
                                    _WHILE6_STATE <= _WHILE6_STATE + 1;
                                    _WHILE <= 0;
                                    _WHILE6_STATE <= 0;
                                end
                            endcase
                        end
                    endcase
                end
            endcase
        end
    end
endmodule
