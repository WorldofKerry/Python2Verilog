import subprocess
import os
import warnings
import pytest
from .utils import Argument

"""
CLI args for pytest
Use dashes instead of underscores in CLI
"""
params = [
    Argument("first_test", False, action="store_true"),
    Argument("write", False, action="store_true"),
]
"""
Other useful flags
-s for output print statements (otherwise they are captured)
-v for verbose
-k "filter" to filter tests
--log-cli-level=DEBUG to enable logging librarys' outputs
"""


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
