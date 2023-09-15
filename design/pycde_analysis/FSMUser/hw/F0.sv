// Generated by CIRCT unknown git version
`include "fsm_enum_typedefs.sv"
module F0(	// /home/kerrwang/repos/testing1/design/pycde_analysis/./mmain.py:78
  input  in0,
         in1,
         in2,
         clk,
         rst,
  output out0,
         out1,
         out2,
         out3
);

     F0_state_t to_idle;	// /home/kerrwang/repos/testing1/design/pycde_analysis/./mmain.py:78
  assign to_idle = F0_state_t_idle;	// /home/kerrwang/repos/testing1/design/pycde_analysis/./mmain.py:78
     F0_state_t to_A;	// /home/kerrwang/repos/testing1/design/pycde_analysis/./mmain.py:78
  assign to_A = F0_state_t_A;	// /home/kerrwang/repos/testing1/design/pycde_analysis/./mmain.py:78
     F0_state_t to_B;	// /home/kerrwang/repos/testing1/design/pycde_analysis/./mmain.py:78
  assign to_B = F0_state_t_B;	// /home/kerrwang/repos/testing1/design/pycde_analysis/./mmain.py:78
     F0_state_t to_C;	// /home/kerrwang/repos/testing1/design/pycde_analysis/./mmain.py:78
  assign to_C = F0_state_t_C;	// /home/kerrwang/repos/testing1/design/pycde_analysis/./mmain.py:78
     F0_state_t state_next;	// /home/kerrwang/repos/testing1/design/pycde_analysis/./mmain.py:78
     F0_state_t state_reg;	// /home/kerrwang/repos/testing1/design/pycde_analysis/./mmain.py:78
  always_ff @(posedge clk) begin	// /home/kerrwang/repos/testing1/design/pycde_analysis/./mmain.py:78
    if (rst)	// /home/kerrwang/repos/testing1/design/pycde_analysis/./mmain.py:78
      state_reg <= to_idle;	// /home/kerrwang/repos/testing1/design/pycde_analysis/./mmain.py:78
    else	// /home/kerrwang/repos/testing1/design/pycde_analysis/./mmain.py:78
      state_reg <= state_next;	// /home/kerrwang/repos/testing1/design/pycde_analysis/./mmain.py:78
  end // always_ff @(posedge)
  reg            output_0;	// /home/kerrwang/repos/testing1/design/pycde_analysis/./mmain.py:78
  reg            output_1;	// /home/kerrwang/repos/testing1/design/pycde_analysis/./mmain.py:78
  reg            output_2;	// /home/kerrwang/repos/testing1/design/pycde_analysis/./mmain.py:78
  reg            output_3;	// /home/kerrwang/repos/testing1/design/pycde_analysis/./mmain.py:78
  always_comb begin	// /home/kerrwang/repos/testing1/design/pycde_analysis/./mmain.py:78
    case (state_reg)	// /home/kerrwang/repos/testing1/design/pycde_analysis/./mmain.py:78
      F0_state_t_idle: begin
        state_next = to_A;	// /home/kerrwang/repos/testing1/design/pycde_analysis/./mmain.py:78
        output_0 = 1'h1;	// /home/kerrwang/repos/testing1/design/pycde_analysis/./mmain.py:78, :117
        output_1 = 1'h0;	// /home/kerrwang/repos/testing1/design/pycde_analysis/./mmain.py:78, :117
        output_2 = 1'h0;	// /home/kerrwang/repos/testing1/design/pycde_analysis/./mmain.py:78, :117
        output_3 = 1'h0;	// /home/kerrwang/repos/testing1/design/pycde_analysis/./mmain.py:78, :117
      end
      F0_state_t_A: begin
        state_next = in0 ? to_B : to_A;	// /home/kerrwang/repos/testing1/design/pycde_analysis/./mmain.py:78
        output_0 = 1'h0;	// /home/kerrwang/repos/testing1/design/pycde_analysis/./mmain.py:78, :117
        output_1 = 1'h1;	// /home/kerrwang/repos/testing1/design/pycde_analysis/./mmain.py:78, :117
        output_2 = 1'h0;	// /home/kerrwang/repos/testing1/design/pycde_analysis/./mmain.py:78, :117
        output_3 = 1'h0;	// /home/kerrwang/repos/testing1/design/pycde_analysis/./mmain.py:78, :117
      end
      F0_state_t_B: begin
        state_next = ~(~(in0 & in1) & ~(in1 & in2) & ~(in0 & in2)) ? to_C : to_B;	// /home/kerrwang/repos/testing1/design/pycde_analysis/./mmain.py:78, :85
        output_0 = 1'h0;	// /home/kerrwang/repos/testing1/design/pycde_analysis/./mmain.py:78, :117
        output_1 = 1'h0;	// /home/kerrwang/repos/testing1/design/pycde_analysis/./mmain.py:78, :117
        output_2 = 1'h1;	// /home/kerrwang/repos/testing1/design/pycde_analysis/./mmain.py:78, :117
        output_3 = 1'h0;	// /home/kerrwang/repos/testing1/design/pycde_analysis/./mmain.py:78, :117
      end
      F0_state_t_C: begin
        state_next = in2 ? to_idle : ~in1 ? to_A : to_C;	// /home/kerrwang/repos/testing1/design/pycde_analysis/./mmain.py:78, :100
        output_0 = 1'h0;	// /home/kerrwang/repos/testing1/design/pycde_analysis/./mmain.py:78, :117
        output_1 = 1'h0;	// /home/kerrwang/repos/testing1/design/pycde_analysis/./mmain.py:78, :117
        output_2 = 1'h0;	// /home/kerrwang/repos/testing1/design/pycde_analysis/./mmain.py:78, :117
        output_3 = 1'h1;	// /home/kerrwang/repos/testing1/design/pycde_analysis/./mmain.py:78, :117
      end
      default: begin
      end
    endcase	// /home/kerrwang/repos/testing1/design/pycde_analysis/./mmain.py:78
  end // always_comb
  assign out0 = output_0;	// /home/kerrwang/repos/testing1/design/pycde_analysis/./mmain.py:78
  assign out1 = output_1;	// /home/kerrwang/repos/testing1/design/pycde_analysis/./mmain.py:78
  assign out2 = output_2;	// /home/kerrwang/repos/testing1/design/pycde_analysis/./mmain.py:78
  assign out3 = output_3;	// /home/kerrwang/repos/testing1/design/pycde_analysis/./mmain.py:78
endmodule
