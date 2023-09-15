// passes ran: builtin.module(cse, canonicalize, cse)
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
    %false = hw.constant false
    %true = hw.constant true
    %C = hw.enum.constant C : !hw.typealias<@fsm_enum_typedecls::@F0_state_t, !hw.enum<idle, A, B, C>>
    %B = hw.enum.constant B : !hw.typealias<@fsm_enum_typedecls::@F0_state_t, !hw.enum<idle, A, B, C>>
    %A = hw.enum.constant A : !hw.typealias<@fsm_enum_typedecls::@F0_state_t, !hw.enum<idle, A, B, C>>
    %idle = hw.enum.constant idle : !hw.typealias<@fsm_enum_typedecls::@F0_state_t, !hw.enum<idle, A, B, C>>
    %to_idle = sv.reg sym @idle : !hw.inout<typealias<@fsm_enum_typedecls::@F0_state_t, !hw.enum<idle, A, B, C>>>
    sv.assign %to_idle, %idle : !hw.typealias<@fsm_enum_typedecls::@F0_state_t, !hw.enum<idle, A, B, C>>
    %0 = sv.read_inout %to_idle : !hw.inout<typealias<@fsm_enum_typedecls::@F0_state_t, !hw.enum<idle, A, B, C>>>
    %to_A = sv.reg sym @A : !hw.inout<typealias<@fsm_enum_typedecls::@F0_state_t, !hw.enum<idle, A, B, C>>>
    sv.assign %to_A, %A : !hw.typealias<@fsm_enum_typedecls::@F0_state_t, !hw.enum<idle, A, B, C>>
    %1 = sv.read_inout %to_A : !hw.inout<typealias<@fsm_enum_typedecls::@F0_state_t, !hw.enum<idle, A, B, C>>>
    %to_B = sv.reg sym @B : !hw.inout<typealias<@fsm_enum_typedecls::@F0_state_t, !hw.enum<idle, A, B, C>>>
    sv.assign %to_B, %B : !hw.typealias<@fsm_enum_typedecls::@F0_state_t, !hw.enum<idle, A, B, C>>
    %2 = sv.read_inout %to_B : !hw.inout<typealias<@fsm_enum_typedecls::@F0_state_t, !hw.enum<idle, A, B, C>>>
    %to_C = sv.reg sym @C : !hw.inout<typealias<@fsm_enum_typedecls::@F0_state_t, !hw.enum<idle, A, B, C>>>
    sv.assign %to_C, %C : !hw.typealias<@fsm_enum_typedecls::@F0_state_t, !hw.enum<idle, A, B, C>>
    %3 = sv.read_inout %to_C : !hw.inout<typealias<@fsm_enum_typedecls::@F0_state_t, !hw.enum<idle, A, B, C>>>
    %state_next = sv.reg : !hw.inout<typealias<@fsm_enum_typedecls::@F0_state_t, !hw.enum<idle, A, B, C>>>
    %4 = sv.read_inout %state_next : !hw.inout<typealias<@fsm_enum_typedecls::@F0_state_t, !hw.enum<idle, A, B, C>>>
    %state_reg = sv.reg : !hw.inout<typealias<@fsm_enum_typedecls::@F0_state_t, !hw.enum<idle, A, B, C>>>
    %5 = sv.read_inout %state_reg : !hw.inout<typealias<@fsm_enum_typedecls::@F0_state_t, !hw.enum<idle, A, B, C>>>
    sv.alwaysff(posedge %clk) {
      sv.passign %state_reg, %4 : !hw.typealias<@fsm_enum_typedecls::@F0_state_t, !hw.enum<idle, A, B, C>>
    }(syncreset : posedge %rst) {
      sv.passign %state_reg, %0 : !hw.typealias<@fsm_enum_typedecls::@F0_state_t, !hw.enum<idle, A, B, C>>
    }
    %6 = comb.mux %in0, %2, %1 : !hw.typealias<@fsm_enum_typedecls::@F0_state_t, !hw.enum<idle, A, B, C>>
    %7 = comb.and bin %in0, %in1 : i1
    %8 = comb.xor bin %7, %true : i1
    %9 = comb.and bin %in1, %in2 : i1
    %10 = comb.xor bin %9, %true : i1
    %11 = comb.and bin %in0, %in2 : i1
    %12 = comb.xor bin %11, %true : i1
    %13 = comb.and bin %8, %10, %12 : i1
    %14 = comb.xor bin %13, %true : i1
    %15 = comb.mux %14, %3, %2 : !hw.typealias<@fsm_enum_typedecls::@F0_state_t, !hw.enum<idle, A, B, C>>
    %16 = comb.xor bin %in1, %true : i1
    %17 = comb.mux %16, %1, %3 : !hw.typealias<@fsm_enum_typedecls::@F0_state_t, !hw.enum<idle, A, B, C>>
    %18 = comb.mux %in2, %0, %17 : !hw.typealias<@fsm_enum_typedecls::@F0_state_t, !hw.enum<idle, A, B, C>>
    %output_0 = sv.reg : !hw.inout<i1>
    %output_1 = sv.reg : !hw.inout<i1>
    %output_2 = sv.reg : !hw.inout<i1>
    %output_3 = sv.reg : !hw.inout<i1>
    sv.alwayscomb {
      sv.case %5 : !hw.typealias<@fsm_enum_typedecls::@F0_state_t, !hw.enum<idle, A, B, C>>
      case idle: {
        sv.bpassign %state_next, %1 : !hw.typealias<@fsm_enum_typedecls::@F0_state_t, !hw.enum<idle, A, B, C>>
        sv.bpassign %output_0, %true : i1
        sv.bpassign %output_1, %false : i1
        sv.bpassign %output_2, %false : i1
        sv.bpassign %output_3, %false : i1
      }
      case A: {
        sv.bpassign %state_next, %6 : !hw.typealias<@fsm_enum_typedecls::@F0_state_t, !hw.enum<idle, A, B, C>>
        sv.bpassign %output_0, %false : i1
        sv.bpassign %output_1, %true : i1
        sv.bpassign %output_2, %false : i1
        sv.bpassign %output_3, %false : i1
      }
      case B: {
        sv.bpassign %state_next, %15 : !hw.typealias<@fsm_enum_typedecls::@F0_state_t, !hw.enum<idle, A, B, C>>
        sv.bpassign %output_0, %false : i1
        sv.bpassign %output_1, %false : i1
        sv.bpassign %output_2, %true : i1
        sv.bpassign %output_3, %false : i1
      }
      case C: {
        sv.bpassign %state_next, %18 : !hw.typealias<@fsm_enum_typedecls::@F0_state_t, !hw.enum<idle, A, B, C>>
        sv.bpassign %output_0, %false : i1
        sv.bpassign %output_1, %false : i1
        sv.bpassign %output_2, %false : i1
        sv.bpassign %output_3, %true : i1
      }
      default: {
      }
    }
    %19 = sv.read_inout %output_0 : !hw.inout<i1>
    %20 = sv.read_inout %output_1 : !hw.inout<i1>
    %21 = sv.read_inout %output_2 : !hw.inout<i1>
    %22 = sv.read_inout %output_3 : !hw.inout<i1>
    hw.output %19, %20, %21, %22 : i1, i1, i1, i1
  }
  sv.verbatim "{\0A  \22declarations\22: [],\0A  \22top_levels\22: [\0A    {\0A      \22module\22: \22@FSMUser\22,\0A      \22services\22: []\0A    }\0A  ],\0A  \22modules\22: []\0A}" {output_file = #hw.output_file<"services.json">}
}
