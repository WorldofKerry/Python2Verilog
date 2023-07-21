import subprocess
import os
import warnings
import pytest


def update_stats(dir: str):
    result = subprocess.run(
        f"python3 tests/update_statistics.py {dir}",
        shell=True,
        capture_output=True,
        # check=True,
        text=True,
    )
    if result.returncode != 0:
        warnings.warn(result.stderr)

    return f"\nStats for {os.path.basename(os.path.basename(os.path.abspath(dir)))}:\n{result.stdout}"


def pytest_sessionfinish(session, exitstatus):
    print(update_stats("tests/integration/data/integration/"))


from .utils import Argument

params = {Argument("all_tests", False)}


def pytest_addoption(parser: pytest.Parser):
    for param in params:
        param.add_to_parser(parser)


@pytest.fixture()
def argparse(request):
    """
    request is a SubRequest for TestCaseFunction
    """
    args = {}
    for param in params:
        args[param.name] = request.config.getoption(f"--{param.dashed_name}")
    setattr(request.cls, "args", type("Args", (object,), args))
