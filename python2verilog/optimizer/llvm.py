import ast

import llvmlite.binding as llvm
from llvmlite import ir

llvm.initialize()
llvm.initialize_native_target()
llvm.initialize_native_asmprinter()


def ast_to_builder(tree, ir_builder: ir.IRBuilder, inputs: dict[str, any], args):
    ast_to_ir = {
        ast.Add: ir_builder.add,
        ast.Sub: ir_builder.sub,
        ast.Mult: ir_builder.mul,
        ast.Div: ir_builder.sdiv,
    }
    for key in inputs:
        inputs[key] = ir_builder.load(inputs[key])

    def rec(node):
        if isinstance(node, ast.Name):
            res = inputs[node.id]
            return res
        if isinstance(node, ast.BinOp):
            res = ast_to_ir[type(node.op)](rec(node.left), rec(node.right))
            return res
        if isinstance(node, ast.Constant):
            return ir.Constant(ir.IntType(32), node.value)
        raise RuntimeError(type(node), ast.dump(node))

    inputs_size = len(inputs)
    for i, assign in enumerate(tree.body):
        res = rec(assign.value)
        ir_builder.store(res, args[inputs_size + i])


def main():
    string = """
second = 7 * (a + b)
first = ((a + b) * (a + b)) - (5 / ((a + b) * (a + b)))
    """
    #     string = """
    # result = ((a + b) * (a + b)) - (5 / ((a + b) * (a + b)))
    # """
    tree = ast.parse(string)
    print(ast.dump(tree, indent="\t"))

    # Create some useful types
    # basic_type = ir.IntType(32)
    basic_type = ir.PointerType(ir.IntType(32))
    fnty = ir.FunctionType(
        ir.VoidType(), (basic_type, basic_type, basic_type, basic_type)
    )

    # Create an empty module...
    module = ir.Module(name="bruv")

    # and declare a function named "fpadd" inside it
    func = ir.Function(module, fnty, name="add")

    # Now implement the function
    block = func.append_basic_block(name="entry")

    llvm_builder = ir.IRBuilder(block)
    inputs = {"a": func.args[0], "b": func.args[1]}
    ast_to_builder(tree, llvm_builder, inputs, func.args)
    llvm_builder.ret_void()

    llmod = llvm.parse_assembly(str(func))
    print(llmod)

    optimize(llmod)
    print(llmod)

    add = llmod.get_function("add")

    def replace_loads(instr: llvm.ValueRef):
        # print(instr._kind)
        instr._kind = "instruction"
        if all([str(instr.opcode) != opcode for opcode in ["load", "store"]]):
            print(instr)
            # print("TRUE")
            # print(instr)
            if instr.opcode:
                for operand in instr.operands:
                    replace_loads(operand)
            # print("TRUE_DONE")
        else:
            # print("mapping", instr)
            # print("FALSE")
            # print(instr)
            if str(instr.opcode) == "store":
                for operand in instr.operands:
                    operand._kind = "instruction"
                    # print("operand", operand, "opcode", operand.opcode)
                    if operand.opcode:
                        # print("operand", operand)
                        replace_loads(operand)
                # print(list(instr.operands))
                for key, input in inputs.items():
                    if f"%{input.name}" in str(instr).strip().split("=")[0]:
                        print(f"{key} -> %{input.name}")
            else:
                print("input", instr)
                for key, input in inputs.items():
                    if f"%{input.name}" in str(instr).strip().split("=")[0]:
                        print(f"{key} -> %{input.name}")

    # print(dir(add))
    code = ""
    print("STARTING CODEGEN")
    mapping = dict(inputs)
    print("mapping", mapping)
    for block in add.blocks:
        for instr in block.instructions:
            if str(instr.opcode) == "store":
                replace_loads(instr)
                print("store", instr)
                continue
            if str(instr.opcode) == "load":
                continue
            code += str(instr) + "\n"
    print("CODE")
    print(code)


def optimize(llmod: llvm.ModuleRef):
    pmb = llvm.create_pass_manager_builder()
    pmb.opt_level = 3
    pm = llvm.create_module_pass_manager()
    pmb.populate(pm)
    pm.run(llmod)


if __name__ == "__main__":
    main()
