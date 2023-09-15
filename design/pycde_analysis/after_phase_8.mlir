// passes ran: builtin.module(convert-fsm-to-sv)
module {
  sv.verbatim "`include \22fsm_enum_typedefs.sv\22"
  hw.type_scope @fsm_enum_typedecls {
    hw.typedecl @F0_state_t : !hw.enum<idle, A, B, C>
  } {output_file = #hw.output_file<"fsm_enum_typedefs.sv">}
  hw.module @FSMUser<__INST_HIER: none = "INSTANTIATE_WITH_INSTANCE_PATH">(%a: i1, %b: i1, %c: i1, %clk: i1, %rst: i1) -> (is_a: i1, is_b: i1, is_c: i1) attributes {output_file = #hw.output_file<"FSMUser.sv", includeReplicatedOps>} {
    %F0.out0, %F0.out1, %F0.out2, %F0.out3 = hw.instance "F0" @F0(in0: %a: i1, in1: %b: i1, in2: %c: i1, clk: %clk: i1, rst: %rst: i1) -> (out0: i1, out1: i1, out2: i1, out3: i1)
    hw.output %F0.out1, %F0.out2, %F0.out3 : i1, i1, i1
  }
  hw.module @F0(%in0: i1, %in1: i1, %in2: i1, %clk: i1, %rst: i1) -> (out0: i1, out1: i1, out2: i1, out3: i1) {
    %idle = hw.enum.constant idle : !hw.typealias<@fsm_enum_typedecls::@F0_state_t, !hw.enum<idle, A, B, C>>
    %to_idle = sv.reg sym @idle : !hw.inout<typealias<@fsm_enum_typedecls::@F0_state_t, !hw.enum<idle, A, B, C>>>
    sv.assign %to_idle, %idle : !hw.typealias<@fsm_enum_typedecls::@F0_state_t, !hw.enum<idle, A, B, C>>
    %0 = sv.read_inout %to_idle : !hw.inout<typealias<@fsm_enum_typedecls::@F0_state_t, !hw.enum<idle, A, B, C>>>
    %A = hw.enum.constant A : !hw.typealias<@fsm_enum_typedecls::@F0_state_t, !hw.enum<idle, A, B, C>>
    %to_A = sv.reg sym @A : !hw.inout<typealias<@fsm_enum_typedecls::@F0_state_t, !hw.enum<idle, A, B, C>>>
    sv.assign %to_A, %A : !hw.typealias<@fsm_enum_typedecls::@F0_state_t, !hw.enum<idle, A, B, C>>
    %1 = sv.read_inout %to_A : !hw.inout<typealias<@fsm_enum_typedecls::@F0_state_t, !hw.enum<idle, A, B, C>>>
    %B = hw.enum.constant B : !hw.typealias<@fsm_enum_typedecls::@F0_state_t, !hw.enum<idle, A, B, C>>
    %to_B = sv.reg sym @B : !hw.inout<typealias<@fsm_enum_typedecls::@F0_state_t, !hw.enum<idle, A, B, C>>>
    sv.assign %to_B, %B : !hw.typealias<@fsm_enum_typedecls::@F0_state_t, !hw.enum<idle, A, B, C>>
    %2 = sv.read_inout %to_B : !hw.inout<typealias<@fsm_enum_typedecls::@F0_state_t, !hw.enum<idle, A, B, C>>>
    %C = hw.enum.constant C : !hw.typealias<@fsm_enum_typedecls::@F0_state_t, !hw.enum<idle, A, B, C>>
    %to_C = sv.reg sym @C : !hw.inout<typealias<@fsm_enum_typedecls::@F0_state_t, !hw.enum<idle, A, B, C>>>
    sv.assign %to_C, %C : !hw.typealias<@fsm_enum_typedecls::@F0_state_t, !hw.enum<idle, A, B, C>>
    %3 = sv.read_inout %to_C : !hw.inout<typealias<@fsm_enum_typedecls::@F0_state_t, !hw.enum<idle, A, B, C>>>
    %state_next = sv.reg : !hw.inout<typealias<@fsm_enum_typedecls::@F0_state_t, !hw.enum<idle, A, B, C>>>
    %4 = sv.read_inout %state_next : !hw.inout<typealias<@fsm_enum_typedecls::@F0_state_t, !hw.enum<idle, A, B, C>>>
    %state_reg = seq.compreg %4, %clk, %rst, %0  : !hw.typealias<@fsm_enum_typedecls::@F0_state_t, !hw.enum<idle, A, B, C>>
    %true = hw.constant true
    %false = hw.constant false
    %false_0 = hw.constant false
    %false_1 = hw.constant false
    %false_2 = hw.constant false
    %true_3 = hw.constant true
    %false_4 = hw.constant false
    %false_5 = hw.constant false
    %5 = comb.mux %in0, %2, %1 : !hw.typealias<@fsm_enum_typedecls::@F0_state_t, !hw.enum<idle, A, B, C>>
    %false_6 = hw.constant false
    %false_7 = hw.constant false
    %true_8 = hw.constant true
    %false_9 = hw.constant false
    %6 = comb.and bin %in0, %in1 : i1
    %true_10 = hw.constant true
    %7 = comb.xor bin %6, %true_10 : i1
    %8 = comb.and bin %in1, %in2 : i1
    %true_11 = hw.constant true
    %9 = comb.xor bin %8, %true_11 : i1
    %10 = comb.and bin %in0, %in2 : i1
    %true_12 = hw.constant true
    %11 = comb.xor bin %10, %true_12 : i1
    %12 = comb.and bin %7, %9, %11 : i1
    %true_13 = hw.constant true
    %13 = comb.xor bin %12, %true_13 : i1
    %14 = comb.mux %13, %3, %2 : !hw.typealias<@fsm_enum_typedecls::@F0_state_t, !hw.enum<idle, A, B, C>>
    %false_14 = hw.constant false
    %false_15 = hw.constant false
    %false_16 = hw.constant false
    %true_17 = hw.constant true
    %true_18 = hw.constant true
    %15 = comb.xor bin %in1, %true_18 : i1
    %16 = comb.mux %15, %1, %3 : !hw.typealias<@fsm_enum_typedecls::@F0_state_t, !hw.enum<idle, A, B, C>>
    %17 = comb.mux %in2, %0, %16 : !hw.typealias<@fsm_enum_typedecls::@F0_state_t, !hw.enum<idle, A, B, C>>
    %output_0 = sv.reg : !hw.inout<i1>
    %output_1 = sv.reg : !hw.inout<i1>
    %output_2 = sv.reg : !hw.inout<i1>
    %output_3 = sv.reg : !hw.inout<i1>
    sv.alwayscomb {
      sv.case %state_reg : !hw.typealias<@fsm_enum_typedecls::@F0_state_t, !hw.enum<idle, A, B, C>>
      case idle: {
        sv.bpassign %state_next, %1 : !hw.typealias<@fsm_enum_typedecls::@F0_state_t, !hw.enum<idle, A, B, C>>
        sv.bpassign %output_0, %true : i1
        sv.bpassign %output_1, %false : i1
        sv.bpassign %output_2, %false_0 : i1
        sv.bpassign %output_3, %false_1 : i1
      }
      case A: {
        sv.bpassign %state_next, %5 : !hw.typealias<@fsm_enum_typedecls::@F0_state_t, !hw.enum<idle, A, B, C>>
        sv.bpassign %output_0, %false_2 : i1
        sv.bpassign %output_1, %true_3 : i1
        sv.bpassign %output_2, %false_4 : i1
        sv.bpassign %output_3, %false_5 : i1
      }
      case B: {
        sv.bpassign %state_next, %14 : !hw.typealias<@fsm_enum_typedecls::@F0_state_t, !hw.enum<idle, A, B, C>>
        sv.bpassign %output_0, %false_6 : i1
        sv.bpassign %output_1, %false_7 : i1
        sv.bpassign %output_2, %true_8 : i1
        sv.bpassign %output_3, %false_9 : i1
      }
      case C: {
        sv.bpassign %state_next, %17 : !hw.typealias<@fsm_enum_typedecls::@F0_state_t, !hw.enum<idle, A, B, C>>
        sv.bpassign %output_0, %false_14 : i1
        sv.bpassign %output_1, %false_15 : i1
        sv.bpassign %output_2, %false_16 : i1
        sv.bpassign %output_3, %true_17 : i1
      }
      default: {
      }
    }
    %18 = sv.read_inout %output_0 : !hw.inout<i1>
    %19 = sv.read_inout %output_1 : !hw.inout<i1>
    %20 = sv.read_inout %output_2 : !hw.inout<i1>
    %21 = sv.read_inout %output_3 : !hw.inout<i1>
    hw.output %18, %19, %20, %21 : i1, i1, i1, i1
  }
  sv.verbatim "{\0A  \22declarations\22: [],\0A  \22top_levels\22: [\0A    {\0A      \22module\22: \22@FSMUser\22,\0A      \22services\22: []\0A    }\0A  ],\0A  \22modules\22: []\0A}" {output_file = #hw.output_file<"services.json">}
}
