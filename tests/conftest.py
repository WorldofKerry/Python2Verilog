import subprocess
import os
import warnings
import pytest
from .utils import Argument

params = [
    Argument("first_test", False, action="store_true"),
    Argument("write", False, action="store_true"),
]


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
