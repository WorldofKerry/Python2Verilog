module happy_face(
    input wire [31:0] radius,
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
    reg signed [31:0] decision;
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
    reg signed [31:0] eye_radius;
    reg signed [31:0] eye_x_offset;
    reg signed [31:0] eye_y_offset;
    reg signed [31:0] i;
    reg signed [31:0] _WHILE11_STATE;
    reg signed [31:0] eye_x;
    reg signed [31:0] eye_y;
    reg signed [31:0] _WHILE11_WHILE;
    reg signed [31:0] _WHILE11_WHILE12_STATE;
    reg signed [31:0] _WHILE11_WHILE12_IF;
    reg signed [31:0] _WHILE11_WHILE12_IF13_STATE;
    reg signed [31:0] _WHILE11_WHILE12_IF14_STATE;
    reg signed [31:0] _WHILE11_WHILE12_IF15_STATE;
    reg signed [31:0] _WHILE11_WHILE12_IF16_STATE;
    reg signed [31:0] _WHILE11_WHILE17_STATE;
    reg signed [31:0] _WHILE11_WHILE17_IF;
    reg signed [31:0] _WHILE11_WHILE17_IF18_STATE;
    reg signed [31:0] _WHILE11_WHILE17_IF19_STATE;
    reg signed [31:0] _WHILE11_WHILE17_IF20_STATE;
    reg signed [31:0] _WHILE11_WHILE17_IF21_STATE;
    reg signed [31:0] _WHILE22_STATE;
    reg signed [31:0] _WHILE22_WHILE;
    reg signed [31:0] _WHILE22_WHILE23_STATE;
    reg signed [31:0] _WHILE22_WHILE23_IF;
    reg signed [31:0] _WHILE22_WHILE23_IF24_STATE;
    reg signed [31:0] _WHILE22_WHILE23_IF25_STATE;
    reg signed [31:0] _WHILE22_WHILE23_IF26_STATE;
    reg signed [31:0] _WHILE22_WHILE23_IF27_STATE;
    reg signed [31:0] _WHILE22_WHILE28_STATE;
    reg signed [31:0] _WHILE22_WHILE28_IF;
    reg signed [31:0] _WHILE22_WHILE28_IF29_STATE;
    reg signed [31:0] _WHILE22_WHILE28_IF30_STATE;
    reg signed [31:0] _WHILE22_WHILE28_IF31_STATE;
    reg signed [31:0] _WHILE22_WHILE28_IF32_STATE;
    reg signed [31:0] smile_radius;
    reg signed [31:0] smile_x_offset;
    reg signed [31:0] smile_y_offset;
    reg signed [31:0] _WHILE33_STATE;
    reg signed [31:0] _WHILE33_IF;
    reg signed [31:0] _WHILE33_IF34_STATE;
    reg signed [31:0] _WHILE33_IF35_STATE;
    reg signed [31:0] _WHILE33_IF36_STATE;
    reg signed [31:0] _WHILE33_IF37_STATE;
    reg signed [31:0] _WHILE38_STATE;
    reg signed [31:0] _WHILE38_IF;
    reg signed [31:0] _WHILE38_IF39_STATE;
    reg signed [31:0] _WHILE38_IF40_STATE;
    reg signed [31:0] _WHILE38_IF41_STATE;
    reg signed [31:0] _WHILE38_IF42_STATE;
    always @(posedge _clock) begin
    _valid <= 0;
        if (_start) begin
            _done <= 0;
            _STATE <= 0;
            x <= 0;
            y <= 0;
            decision <= 0;
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
            eye_radius <= 0;
            eye_x_offset <= 0;
            eye_y_offset <= 0;
            i <= 0;
            _WHILE11_STATE <= 0;
            eye_x <= 0;
            eye_y <= 0;
            _WHILE11_WHILE <= 0;
            _WHILE11_WHILE12_STATE <= 0;
            _WHILE11_WHILE12_IF <= 0;
            _WHILE11_WHILE12_IF13_STATE <= 0;
            _WHILE11_WHILE12_IF14_STATE <= 0;
            _WHILE11_WHILE12_IF15_STATE <= 0;
            _WHILE11_WHILE12_IF16_STATE <= 0;
            _WHILE11_WHILE17_STATE <= 0;
            _WHILE11_WHILE17_IF <= 0;
            _WHILE11_WHILE17_IF18_STATE <= 0;
            _WHILE11_WHILE17_IF19_STATE <= 0;
            _WHILE11_WHILE17_IF20_STATE <= 0;
            _WHILE11_WHILE17_IF21_STATE <= 0;
            _WHILE22_STATE <= 0;
            _WHILE22_WHILE <= 0;
            _WHILE22_WHILE23_STATE <= 0;
            _WHILE22_WHILE23_IF <= 0;
            _WHILE22_WHILE23_IF24_STATE <= 0;
            _WHILE22_WHILE23_IF25_STATE <= 0;
            _WHILE22_WHILE23_IF26_STATE <= 0;
            _WHILE22_WHILE23_IF27_STATE <= 0;
            _WHILE22_WHILE28_STATE <= 0;
            _WHILE22_WHILE28_IF <= 0;
            _WHILE22_WHILE28_IF29_STATE <= 0;
            _WHILE22_WHILE28_IF30_STATE <= 0;
            _WHILE22_WHILE28_IF31_STATE <= 0;
            _WHILE22_WHILE28_IF32_STATE <= 0;
            smile_radius <= 0;
            smile_x_offset <= 0;
            smile_y_offset <= 0;
            _WHILE33_STATE <= 0;
            _WHILE33_IF <= 0;
            _WHILE33_IF34_STATE <= 0;
            _WHILE33_IF35_STATE <= 0;
            _WHILE33_IF36_STATE <= 0;
            _WHILE33_IF37_STATE <= 0;
            _WHILE38_STATE <= 0;
            _WHILE38_IF <= 0;
            _WHILE38_IF39_STATE <= 0;
            _WHILE38_IF40_STATE <= 0;
            _WHILE38_IF41_STATE <= 0;
            _WHILE38_IF42_STATE <= 0;
        end else begin
            case (_STATE)
                0: begin
                    x <= 0;
                    _STATE <= _STATE + 1;
                end
                1: begin
                    y <= radius;
                    _STATE <= _STATE + 1;
                end
                2: begin
                    decision <= (3 - (2 * radius));
                    _STATE <= _STATE + 1;
                end
                3: begin
                    case (_WHILE)
                        0: begin
                            if (!(x <= y)) begin     _STATE <= _STATE + 1; end else begin     _WHILE <= 1; end
                        end
                        1: begin
                            case (_WHILE6_STATE)
                                0: begin
                                    _out0 <= x;
                                    _out1 <= y;
                                    _valid <= 1;
                                    _WHILE6_STATE <= _WHILE6_STATE + 1;
                                end
                                1: begin
                                    _out0 <= -(x);
                                    _out1 <= y;
                                    _valid <= 1;
                                    _WHILE6_STATE <= _WHILE6_STATE + 1;
                                end
                                2: begin
                                    _out0 <= x;
                                    _out1 <= -(y);
                                    _valid <= 1;
                                    _WHILE6_STATE <= _WHILE6_STATE + 1;
                                end
                                3: begin
                                    _out0 <= -(x);
                                    _out1 <= -(y);
                                    _valid <= 1;
                                    _WHILE6_STATE <= _WHILE6_STATE + 1;
                                end
                                4: begin
                                    _out0 <= y;
                                    _out1 <= x;
                                    _valid <= 1;
                                    _WHILE6_STATE <= _WHILE6_STATE + 1;
                                end
                                5: begin
                                    _out0 <= -(y);
                                    _out1 <= x;
                                    _valid <= 1;
                                    _WHILE6_STATE <= _WHILE6_STATE + 1;
                                end
                                6: begin
                                    _out0 <= y;
                                    _out1 <= -(x);
                                    _valid <= 1;
                                    _WHILE6_STATE <= _WHILE6_STATE + 1;
                                end
                                7: begin
                                    _out0 <= -(y);
                                    _out1 <= -(x);
                                    _valid <= 1;
                                    _WHILE6_STATE <= _WHILE6_STATE + 1;
                                end
                                8: begin
                                    case (_WHILE6_IF)
                                        0: begin
                                            if (decision < 0)
                                            _WHILE6_IF <= 1;
                                            else _WHILE6_IF <= 2;
                                        end
                                        1: begin
                                            case (_WHILE6_IF9_STATE)
                                                0: begin
                                                    decision <= (decision + ((4 * x) + 6));
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
                                                    decision <= (decision + ((4 * (x - y)) + 10));
                                                    _WHILE6_IF10_STATE <= _WHILE6_IF10_STATE + 1;
                                                end
                                                1: begin
                                                    y <= (y - 1);
                                                    _WHILE6_IF10_STATE <= _WHILE6_IF10_STATE + 1;
                                                    _WHILE6_STATE <= _WHILE6_STATE + 1;
                                                    _WHILE6_IF <= 0;
                                                    _WHILE6_IF10_STATE <= 0;
                                                end
                                            endcase
                                        end
                                    endcase
                                end
                                9: begin
                                    x <= (x + 1);
                                    _WHILE6_STATE <= _WHILE6_STATE + 1;
                                    _WHILE <= 0;
                                    _WHILE6_STATE <= 0;
                                end
                            endcase
                        end
                    endcase
                end
                4: begin
                    eye_radius <= (radius / 5);
                    _STATE <= _STATE + 1;
                end
                5: begin
                    eye_x_offset <= (radius / 3);
                    _STATE <= _STATE + 1;
                end
                6: begin
                    eye_y_offset <= (radius / 3);
                    _STATE <= _STATE + 1;
                end
                7: begin
                    i <= -(1);
                    _STATE <= _STATE + 1;
                end
                8: begin
                    case (_WHILE)
                        0: begin
                            if (!(i <= 1)) begin     _STATE <= _STATE + 1; end else begin     _WHILE <= 1; end
                        end
                        1: begin
                            case (_WHILE22_STATE)
                                0: begin
                                    eye_x <= (i * eye_x_offset);
                                    _WHILE22_STATE <= _WHILE22_STATE + 1;
                                end
                                1: begin
                                    eye_y <= eye_y_offset;
                                    _WHILE22_STATE <= _WHILE22_STATE + 1;
                                end
                                2: begin
                                    decision <= (3 - (2 * eye_radius));
                                    _WHILE22_STATE <= _WHILE22_STATE + 1;
                                end
                                3: begin
                                    x <= 0;
                                    _WHILE22_STATE <= _WHILE22_STATE + 1;
                                end
                                4: begin
                                    y <= eye_radius;
                                    _WHILE22_STATE <= _WHILE22_STATE + 1;
                                end
                                5: begin
                                    case (_WHILE22_WHILE)
                                        0: begin
                                            if (!(x <= y)) begin     _WHILE22_STATE <= _WHILE22_STATE + 1; end else begin     _WHILE22_WHILE <= 1; end
                                        end
                                        1: begin
                                            case (_WHILE22_WHILE28_STATE)
                                                0: begin
                                                    _out0 <= (eye_x + x);
                                                    _out1 <= (eye_y + y);
                                                    _valid <= 1;
                                                    _WHILE22_WHILE28_STATE <= _WHILE22_WHILE28_STATE + 1;
                                                end
                                                1: begin
                                                    _out0 <= (eye_x - x);
                                                    _out1 <= (eye_y + y);
                                                    _valid <= 1;
                                                    _WHILE22_WHILE28_STATE <= _WHILE22_WHILE28_STATE + 1;
                                                end
                                                2: begin
                                                    _out0 <= (eye_x + x);
                                                    _out1 <= (eye_y - y);
                                                    _valid <= 1;
                                                    _WHILE22_WHILE28_STATE <= _WHILE22_WHILE28_STATE + 1;
                                                end
                                                3: begin
                                                    _out0 <= (eye_x - x);
                                                    _out1 <= (eye_y - y);
                                                    _valid <= 1;
                                                    _WHILE22_WHILE28_STATE <= _WHILE22_WHILE28_STATE + 1;
                                                end
                                                4: begin
                                                    _out0 <= (eye_x + y);
                                                    _out1 <= (eye_y + x);
                                                    _valid <= 1;
                                                    _WHILE22_WHILE28_STATE <= _WHILE22_WHILE28_STATE + 1;
                                                end
                                                5: begin
                                                    _out0 <= (eye_x - y);
                                                    _out1 <= (eye_y + x);
                                                    _valid <= 1;
                                                    _WHILE22_WHILE28_STATE <= _WHILE22_WHILE28_STATE + 1;
                                                end
                                                6: begin
                                                    _out0 <= (eye_x + y);
                                                    _out1 <= (eye_y - x);
                                                    _valid <= 1;
                                                    _WHILE22_WHILE28_STATE <= _WHILE22_WHILE28_STATE + 1;
                                                end
                                                7: begin
                                                    _out0 <= (eye_x - y);
                                                    _out1 <= (eye_y - x);
                                                    _valid <= 1;
                                                    _WHILE22_WHILE28_STATE <= _WHILE22_WHILE28_STATE + 1;
                                                end
                                                8: begin
                                                    case (_WHILE22_WHILE28_IF)
                                                        0: begin
                                                            if (decision < 0)
                                                            _WHILE22_WHILE28_IF <= 1;
                                                            else _WHILE22_WHILE28_IF <= 2;
                                                        end
                                                        1: begin
                                                            case (_WHILE22_WHILE28_IF31_STATE)
                                                                0: begin
                                                                    decision <= (decision + ((4 * x) + 6));
                                                                    _WHILE22_WHILE28_IF31_STATE <= _WHILE22_WHILE28_IF31_STATE + 1;
                                                                    _WHILE22_WHILE28_STATE <= _WHILE22_WHILE28_STATE + 1;
                                                                    _WHILE22_WHILE28_IF <= 0;
                                                                    _WHILE22_WHILE28_IF31_STATE <= 0;
                                                                end
                                                            endcase
                                                        end
                                                        2: begin
                                                            case (_WHILE22_WHILE28_IF32_STATE)
                                                                0: begin
                                                                    decision <= (decision + ((4 * (x - y)) + 10));
                                                                    _WHILE22_WHILE28_IF32_STATE <= _WHILE22_WHILE28_IF32_STATE + 1;
                                                                end
                                                                1: begin
                                                                    y <= (y - 1);
                                                                    _WHILE22_WHILE28_IF32_STATE <= _WHILE22_WHILE28_IF32_STATE + 1;
                                                                    _WHILE22_WHILE28_STATE <= _WHILE22_WHILE28_STATE + 1;
                                                                    _WHILE22_WHILE28_IF <= 0;
                                                                    _WHILE22_WHILE28_IF32_STATE <= 0;
                                                                end
                                                            endcase
                                                        end
                                                    endcase
                                                end
                                                9: begin
                                                    x <= (x + 1);
                                                    _WHILE22_WHILE28_STATE <= _WHILE22_WHILE28_STATE + 1;
                                                    _WHILE22_WHILE <= 0;
                                                    _WHILE22_WHILE28_STATE <= 0;
                                                end
                                            endcase
                                        end
                                    endcase
                                end
                                6: begin
                                    i <= (i + 2);
                                    _WHILE22_STATE <= _WHILE22_STATE + 1;
                                    _WHILE <= 0;
                                    _WHILE22_STATE <= 0;
                                end
                            endcase
                        end
                    endcase
                end
                9: begin
                    smile_radius <= (radius / 2);
                    _STATE <= _STATE + 1;
                end
                10: begin
                    smile_x_offset <= 0;
                    _STATE <= _STATE + 1;
                end
                11: begin
                    smile_y_offset <= (-(smile_radius) / 2);
                    _STATE <= _STATE + 1;
                end
                12: begin
                    x <= 0;
                    _STATE <= _STATE + 1;
                end
                13: begin
                    y <= smile_radius;
                    _STATE <= _STATE + 1;
                end
                14: begin
                    decision <= (3 - (2 * smile_radius));
                    _STATE <= _STATE + 1;
                end
                15: begin
                    case (_WHILE)
                        0: begin
                            if (!(x <= y)) begin     _STATE <= _STATE + 1;     _done <= 1; end else begin     _WHILE <= 1; end
                        end
                        1: begin
                            case (_WHILE38_STATE)
                                0: begin
                                    _out0 <= (smile_x_offset + x);
                                    _out1 <= (smile_y_offset + y);
                                    _valid <= 1;
                                    _WHILE38_STATE <= _WHILE38_STATE + 1;
                                end
                                1: begin
                                    _out0 <= (smile_x_offset - x);
                                    _out1 <= (smile_y_offset + y);
                                    _valid <= 1;
                                    _WHILE38_STATE <= _WHILE38_STATE + 1;
                                end
                                2: begin
                                    case (_WHILE38_IF)
                                        0: begin
                                            if (decision < 0)
                                            _WHILE38_IF <= 1;
                                            else _WHILE38_IF <= 2;
                                        end
                                        1: begin
                                            case (_WHILE38_IF41_STATE)
                                                0: begin
                                                    decision <= (decision + ((4 * x) + 6));
                                                    _WHILE38_IF41_STATE <= _WHILE38_IF41_STATE + 1;
                                                    _WHILE38_STATE <= _WHILE38_STATE + 1;
                                                    _WHILE38_IF <= 0;
                                                    _WHILE38_IF41_STATE <= 0;
                                                end
                                            endcase
                                        end
                                        2: begin
                                            case (_WHILE38_IF42_STATE)
                                                0: begin
                                                    decision <= (decision + ((4 * (x - y)) + 10));
                                                    _WHILE38_IF42_STATE <= _WHILE38_IF42_STATE + 1;
                                                end
                                                1: begin
                                                    y <= (y - 1);
                                                    _WHILE38_IF42_STATE <= _WHILE38_IF42_STATE + 1;
                                                    _WHILE38_STATE <= _WHILE38_STATE + 1;
                                                    _WHILE38_IF <= 0;
                                                    _WHILE38_IF42_STATE <= 0;
                                                end
                                            endcase
                                        end
                                    endcase
                                end
                                3: begin
                                    x <= (x + 1);
                                    _WHILE38_STATE <= _WHILE38_STATE + 1;
                                    _WHILE <= 0;
                                    _WHILE38_STATE <= 0;
                                end
                            endcase
                        end
                    endcase
                end
            endcase
        end
    end
endmodule
