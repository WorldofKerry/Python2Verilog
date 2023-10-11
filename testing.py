import tempfile
from importlib import util

from python2verilog.api.namespace import namespace_to_verilog, new_namespace

raw = """
@verilogify
def func() -> int:
    yield 123
    """
raw = "from python2verilog import verilogify\n" + raw

# Create a temporary source code file
with tempfile.NamedTemporaryFile(suffix=".py") as tmp:
    tmp.write(raw.encode())
    tmp.flush()

    # Now load that file as a module
    try:
        spec = util.spec_from_file_location("tmp", tmp.name)
        module = util.module_from_spec(spec)
        spec.loader.exec_module(module)

        # ...or, while the tmp file exists, you can query it externally
        ns = new_namespace(tmp.name)
        module, _ = namespace_to_verilog(ns)
        print(module)

    except Exception as e:
        print(e)
