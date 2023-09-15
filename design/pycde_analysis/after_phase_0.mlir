// passes ran: builtin.module(esi-connect-services)
module {
  msft.module @FSMUser {} (%a: i1, %b: i1, %c: i1, %clk: i1, %rst: i1) -> (is_a: i1, is_b: i1, is_c: i1) attributes {fileName = "FSMUser.sv"} {
    %0:4 = fsm.hw_instance "F0" @F0(%a, %b, %c), clock %clk, reset %rst : (i1, i1, i1) -> (i1, i1, i1, i1)
    msft.output %0#1, %0#2, %0#3 : i1, i1, i1
  }
  fsm.machine @F0(%arg0: i1, %arg1: i1, %arg2: i1) -> (i1, i1, i1, i1) attributes {clock_name = "clk", in_names = ["a", "b", "c"], initialState = "idle", out_names = ["is_idle", "is_A", "is_B", "is_C"], reset_name = "rst"} {
    fsm.state @idle output {
      %true = hw.constant true
      %false = hw.constant false
      %false_0 = hw.constant false
      %false_1 = hw.constant false
      fsm.output %true, %false, %false_0, %false_1 : i1, i1, i1, i1
    } transitions {
      fsm.transition @A
    }
    fsm.state @A output {
      %false = hw.constant false
      %true = hw.constant true
      %false_0 = hw.constant false
      %false_1 = hw.constant false
      fsm.output %false, %true, %false_0, %false_1 : i1, i1, i1, i1
    } transitions {
      fsm.transition @B guard {
        fsm.return %arg0
      }
    }
    fsm.state @B output {
      %false = hw.constant false
      %false_0 = hw.constant false
      %true = hw.constant true
      %false_1 = hw.constant false
      fsm.output %false, %false_0, %true, %false_1 : i1, i1, i1, i1
    } transitions {
      fsm.transition @C guard {
        %0 = comb.and bin %arg0, %arg1 : i1
        %true = hw.constant true
        %1 = comb.xor bin %0, %true : i1
        %2 = comb.and bin %arg1, %arg2 : i1
        %true_0 = hw.constant true
        %3 = comb.xor bin %2, %true_0 : i1
        %4 = comb.and bin %arg0, %arg2 : i1
        %true_1 = hw.constant true
        %5 = comb.xor bin %4, %true_1 : i1
        %6 = comb.and bin %1, %3, %5 : i1
        %true_2 = hw.constant true
        %7 = comb.xor bin %6, %true_2 : i1
        fsm.return %7
      }
    }
    fsm.state @C output {
      %false = hw.constant false
      %false_0 = hw.constant false
      %false_1 = hw.constant false
      %true = hw.constant true
      fsm.output %false, %false_0, %false_1, %true : i1, i1, i1, i1
    } transitions {
      fsm.transition @idle guard {
        fsm.return %arg2
      }
      fsm.transition @A guard {
        %true = hw.constant true
        %0 = comb.xor bin %arg1, %true : i1
        fsm.return %0
      }
    }
  }
}
