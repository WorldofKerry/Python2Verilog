module draw_rectangle(
    input wire _clock,
    input wire _start,
    input wire signed [31:0] s_x,
    input wire signed [31:0] s_y,
    input wire signed [31:0] height,
    input wire signed [31:0] width,
    output reg signed [31:0] _out0,
    output reg signed [31:0] _out1,
    output reg _done
);
    reg signed [31:0] _STATE;
    reg signed [31:0] _STATE_0;
    reg signed [31:0] x;
    reg signed [31:0] _STATE_1;
    reg signed [31:0] y;
    reg signed [31:0] _STATE_2;
    reg signed [31:0] d;
    reg signed [31:0] _STATE_3;
    reg signed [31:0] _STATE_4;
    reg signed [31:0] _STATE_5;
    reg signed [31:0] _STATE_6;
    reg signed [31:0] _STATE_7;
    reg signed [31:0] _STATE_8;
    reg signed [31:0] _STATE_9;
    reg signed [31:0] _STATE_10;
    reg signed [31:0] _STATE_11;
    reg signed [31:0] _BODY_1_STATE;
    reg signed [31:0] _BODY_1_STATE_0;
    reg signed [31:0] _BODY_1_STATE_1;
    reg signed [31:0] _BODY_1_IF;
    reg signed [31:0] _BODY_1_IF_CONDITIONAL;
    reg signed [31:0] _BODY_1_IF_THEN;
    reg signed [31:0] _BODY_1_IF_ELSE;
    reg signed [31:0] _BODY_1_IF_2_STATE;
    reg signed [31:0] _BODY_1_IF_2_STATE_0;
    reg signed [31:0] _BODY_1_IF_2_STATE_1;
    reg signed [31:0] _BODY_1_IF_2_STATE_2;
    reg signed [31:0] _BODY_1_IF_3_STATE;
    reg signed [31:0] _BODY_1_IF_3_STATE_0;
    reg signed [31:0] _BODY_1_IF_3_STATE_1;
    reg signed [31:0] _BODY_1_STATE_2;
    reg signed [31:0] _BODY_1_STATE_3;
    reg signed [31:0] _BODY_1_STATE_4;
    reg signed [31:0] _BODY_1_STATE_5;
    reg signed [31:0] _BODY_1_STATE_6;
    reg signed [31:0] _BODY_1_STATE_7;
    reg signed [31:0] _BODY_1_STATE_8;
    reg signed [31:0] _BODY_1_STATE_9;
    reg signed [31:0] _STATE_12;
        always @(posedge _clock) begin
            if (_start) begin
                _done <= 0;
                _STATE <= 0;
                _STATE_0 <= 0;
                x <= 0;
                _STATE_1 <= 1;
                y <= 0;
                _STATE_2 <= 2;
                d <= 0;
                _STATE_3 <= 3;
                _STATE_4 <= 4;
                _STATE_5 <= 5;
                _STATE_6 <= 6;
                _STATE_7 <= 7;
                _STATE_8 <= 8;
                _STATE_9 <= 9;
                _STATE_10 <= 10;
                _STATE_11 <= 11;
                _BODY_1_STATE <= 0;
                _BODY_1_STATE_0 <= 0;
                _BODY_1_STATE_1 <= 1;
                _BODY_1_IF <= 0;
                _BODY_1_IF_CONDITIONAL <= 0;
                _BODY_1_IF_THEN <= 1;
                _BODY_1_IF_ELSE <= 2;
                _BODY_1_IF_2_STATE <= 0;
                _BODY_1_IF_2_STATE_0 <= 0;
                _BODY_1_IF_2_STATE_1 <= 1;
                _BODY_1_IF_2_STATE_2 <= 2;
                _BODY_1_IF_3_STATE <= 0;
                _BODY_1_IF_3_STATE_0 <= 0;
                _BODY_1_IF_3_STATE_1 <= 1;
                _BODY_1_STATE_2 <= 2;
                _BODY_1_STATE_3 <= 3;
                _BODY_1_STATE_4 <= 4;
                _BODY_1_STATE_5 <= 5;
                _BODY_1_STATE_6 <= 6;
                _BODY_1_STATE_7 <= 7;
                _BODY_1_STATE_8 <= 8;
                _BODY_1_STATE_9 <= 9;
                _STATE_12 <= 12;
            end else begin
                case (_STATE) // STATEMENTS START
                    _STATE_0: begin
                        x <= 0;
                        _STATE <= _STATE + 1; // INCREMENT STATE
                    end
                    _STATE_1: begin
                        y <= height;
                        _STATE <= _STATE + 1; // INCREMENT STATE
                    end
                    _STATE_2: begin
                        d <= (3 - (2 * height));
                        _STATE <= _STATE + 1; // INCREMENT STATE
                    end
                    _STATE_3: begin
                        _out0 <= (s_x + x);
                        _out1 <= (s_y + y);
                        _STATE <= _STATE + 1; // INCREMENT STATE
                    end
                    _STATE_4: begin
                        _out0 <= (s_x + x);
                        _out1 <= (s_y - y);
                        _STATE <= _STATE + 1; // INCREMENT STATE
                    end
                    _STATE_5: begin
                        _out0 <= (s_x - x);
                        _out1 <= (s_y + y);
                        _STATE <= _STATE + 1; // INCREMENT STATE
                    end
                    _STATE_6: begin
                        _out0 <= (s_x - x);
                        _out1 <= (s_y - y);
                        _STATE <= _STATE + 1; // INCREMENT STATE
                    end
                    _STATE_7: begin
                        _out0 <= (s_x + y);
                        _out1 <= (s_y + x);
                        _STATE <= _STATE + 1; // INCREMENT STATE
                    end
                    _STATE_8: begin
                        _out0 <= (s_x + y);
                        _out1 <= (s_y - x);
                        _STATE <= _STATE + 1; // INCREMENT STATE
                    end
                    _STATE_9: begin
                        _out0 <= (s_x - y);
                        _out1 <= (s_y + x);
                        _STATE <= _STATE + 1; // INCREMENT STATE
                    end
                    _STATE_10: begin
                        _out0 <= (s_x - y);
                        _out1 <= (s_y - x);
                        _STATE <= _STATE + 1; // INCREMENT STATE
                    end
                    _STATE_11: begin
                        if (!(y >= x)) begin // WHILE LOOP START
                            _STATE = _STATE + 1;
                        end else begin
                            case (_BODY_1_STATE) // STATEMENTS START
                                _BODY_1_STATE_0: begin
                                    x <= (x + 1);
                                    _BODY_1_STATE <= _BODY_1_STATE + 1; // INCREMENT STATE
                                end
                                _BODY_1_STATE_1: begin
                                    case (_BODY_1_IF) // IF START
                                        _BODY_1_IF_CONDITIONAL: begin
                                            if (d > 0) _BODY_1_IF <= _BODY_1_IF_THEN;
                                            else _BODY_1_IF <= _BODY_1_IF_ELSE;
                                        end
                                        _BODY_1_IF_THEN: begin
                                            case (_BODY_1_IF_2_STATE) // STATEMENTS START
                                                _BODY_1_IF_2_STATE_0: begin
                                                    y <= (y - 1);
                                                    _BODY_1_IF_2_STATE <= _BODY_1_IF_2_STATE + 1; // INCREMENT STATE
                                                end
                                                _BODY_1_IF_2_STATE_1: begin
                                                    d <= ((d + (4 * (x - y))) + 10);
                                                    _BODY_1_IF_2_STATE <= _BODY_1_IF_2_STATE + 1; // INCREMENT STATE
                                                end
                                                _BODY_1_IF_2_STATE_2: begin // END STATEMENTS STATE
                                                    _BODY_1_STATE <= _BODY_1_STATE + 1; _BODY_1_IF <= _BODY_1_IF_CONDITIONAL;
                                                    _BODY_1_IF_2_STATE <= 0; // LOOP FOR LOOP STATEMENTS
                                                end
                                            endcase // STATEMENTS END
                                        end
                                        _BODY_1_IF_ELSE: begin
                                            case (_BODY_1_IF_3_STATE) // STATEMENTS START
                                                _BODY_1_IF_3_STATE_0: begin
                                                    d <= ((d + (4 * x)) + 6);
                                                    _BODY_1_IF_3_STATE <= _BODY_1_IF_3_STATE + 1; // INCREMENT STATE
                                                end
                                                _BODY_1_IF_3_STATE_1: begin // END STATEMENTS STATE
                                                    _BODY_1_STATE <= _BODY_1_STATE + 1; _BODY_1_IF <= _BODY_1_IF_CONDITIONAL;
                                                    _BODY_1_IF_3_STATE <= 0; // LOOP FOR LOOP STATEMENTS
                                                end
                                            endcase // STATEMENTS END
                                        end
                                    endcase // IF END
                                end
                                _BODY_1_STATE_2: begin
                                    _out0 <= (s_x + x);
                                    _out1 <= (s_y + y);
                                    _BODY_1_STATE <= _BODY_1_STATE + 1; // INCREMENT STATE
                                end
                                _BODY_1_STATE_3: begin
                                    _out0 <= (s_x + x);
                                    _out1 <= (s_y - y);
                                    _BODY_1_STATE <= _BODY_1_STATE + 1; // INCREMENT STATE
                                end
                                _BODY_1_STATE_4: begin
                                    _out0 <= (s_x - x);
                                    _out1 <= (s_y + y);
                                    _BODY_1_STATE <= _BODY_1_STATE + 1; // INCREMENT STATE
                                end
                                _BODY_1_STATE_5: begin
                                    _out0 <= (s_x - x);
                                    _out1 <= (s_y - y);
                                    _BODY_1_STATE <= _BODY_1_STATE + 1; // INCREMENT STATE
                                end
                                _BODY_1_STATE_6: begin
                                    _out0 <= (s_x + y);
                                    _out1 <= (s_y + x);
                                    _BODY_1_STATE <= _BODY_1_STATE + 1; // INCREMENT STATE
                                end
                                _BODY_1_STATE_7: begin
                                    _out0 <= (s_x + y);
                                    _out1 <= (s_y - x);
                                    _BODY_1_STATE <= _BODY_1_STATE + 1; // INCREMENT STATE
                                end
                                _BODY_1_STATE_8: begin
                                    _out0 <= (s_x - y);
                                    _out1 <= (s_y + x);
                                    _BODY_1_STATE <= _BODY_1_STATE + 1; // INCREMENT STATE
                                end
                                _BODY_1_STATE_9: begin
                                    _out0 <= (s_x - y);
                                    _out1 <= (s_y - x);
                                    _BODY_1_STATE <= _BODY_1_STATE + 1; // INCREMENT STATE
                                    _BODY_1_STATE <= 0; // LOOP FOR LOOP STATEMENTS
                                end
                            endcase // STATEMENTS END
                        end // WHILE LOOP END
                    end
                    _STATE_12: begin // END STATEMENTS STATE
                        _done = 1;
                    end
                endcase // STATEMENTS END
            end
        end
endmodule
