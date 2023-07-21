import subprocess
import os
import warnings


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
