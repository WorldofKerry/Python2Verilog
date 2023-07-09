module draw_rectangle(
    input wire _clock,
    input wire _start,
    input wire [31:0] s_x,
    input wire [31:0] s_y,
    input wire [31:0] height,
    input wire [31:0] width,
    output reg [31:0] _out0,
    output reg [31:0] _out1,
    output reg _done
);
    reg [31:0] _STATE;
    reg [31:0] _STATE_0;
    reg [31:0] counter;
    reg [31:0] _STATE_1;
    reg [31:0] _INNER_1_STATE;
    reg [31:0] _INNER_1_STATE_0;
    reg [31:0] _INNER_1_STATE_1;
    reg [31:0] _STATE_2;
        always @(posedge _clock) begin
            if (_start) begin
                _done <= 0;
                _STATE <= 0;
                _STATE_0 <= 0;
                counter <= 0;
                _STATE_1 <= 1;
                _INNER_1_STATE <= 0;
                _INNER_1_STATE_0 <= 0;
                _INNER_1_STATE_1 <= 1;
                _STATE_2 <= 2;
            end else begin
                case (_STATE) // STATEMENTS START
                    _STATE_0: begin
                        counter <= 0;
                        _STATE <= _STATE + 1; // INCREMENT STATE
                    end
                    _STATE_1: begin
                        if (!(counter < height)) begin // WHILE LOOP START
                            _STATE = _STATE + 1;
                        end else begin
                            case (_INNER_1_STATE) // STATEMENTS START
                                _INNER_1_STATE_0: begin
                                    _out0 <= counter;
                                    _out1 <= counter;
                                    _INNER_1_STATE <= _INNER_1_STATE + 1; // INCREMENT STATE
                                end
                                _INNER_1_STATE_1: begin
                                    counter <= counter + 1;
                                    _INNER_1_STATE <= _INNER_1_STATE + 1; // INCREMENT STATE
                                    _INNER_1_STATE <= 0; // LOOP FOR LOOP STATEMENTS
                                end
                            endcase // STATEMENTS END
                        end // WHILE LOOP END
                    end
                    _STATE_2: begin // END STATEMENTS STATE
                        _done = 1;
                    end
                endcase // STATEMENTS END
            end
        end
endmodule
