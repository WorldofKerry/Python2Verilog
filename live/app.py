import tempfile
import traceback
from importlib import util

from flask import Flask, jsonify, render_template, request

from python2verilog import py_to_verilog
from python2verilog.api.namespace import get_namespace, namespace_to_verilog

app = Flask(__name__)


@app.route("/")
def index():
    return render_template("index.html")


def tempfile_wrapper(raw: str):
    raw = "from python2verilog import verilogify\n" + raw

    # Create a temporary source code file
    with tempfile.NamedTemporaryFile(suffix=".py") as tmp:
        tmp.write(raw.encode())
        tmp.flush()

        try:
            spec = util.spec_from_file_location("tmp", tmp.name)
            module = util.module_from_spec(spec)
            spec.loader.exec_module(module)

            ns = get_namespace(tmp.name)
            result, _ = namespace_to_verilog(ns)
        except Exception:
            result = traceback.format_exc(limit=1)
        finally:
            return result


@app.route("/update_text", methods=["POST"])
def update_text():
    text = request.form["text"]
    text = tempfile_wrapper(text)
    updated_text = text
    return jsonify(updated_text=updated_text)


if __name__ == "__main__":
    app.run(debug=True)
