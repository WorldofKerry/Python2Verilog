import tempfile
from importlib import util

from flask import Flask, jsonify, render_template, request

from python2verilog import py_to_verilog
from python2verilog.api.namespace import get_namespace, namespace_to_verilog

app = Flask(__name__)


@app.route("/")
def index():
    return render_template("index.html")


def wrapper(input: str):
    """
    Closure for running the exec
    """
    input = """
def fib() -> int:
  a, b = 0, 1
  while a < 30:
    yield a
    a, b = b, a + b
"""
    module, tb = py_to_verilog(
        input, "fib", extra_test_cases=[], file_path="./flask_testing"
    )
    print(module)


def tempfile_wrapper(raw: str):
    raw = "from python2verilog import verilogify\n" + raw

    # Create a temporary source code file
    with tempfile.NamedTemporaryFile(suffix=".py") as tmp:
        tmp.write(raw.encode())
        tmp.flush()

        # Now load that file as a module
        spec = util.spec_from_file_location("tmp", tmp.name)
        module = util.module_from_spec(spec)
        spec.loader.exec_module(module)

        # ...or, while the tmp file exists, you can query it externally
        import inspect

        print(inspect.getsource(module.fib))

        ns = get_namespace(tmp.name)
        module, _ = namespace_to_verilog(ns)
        return module


@app.route("/update_text", methods=["POST"])
def update_text():
    text = request.form["text"]
    # You can process the text here as needed
    # For this example, we'll just convert it to uppercase
    # out = wrapper(text)
    result = tempfile_wrapper(text)
    updated_text = result
    return jsonify(updated_text=updated_text)


if __name__ == "__main__":
    app.run(debug=True)
