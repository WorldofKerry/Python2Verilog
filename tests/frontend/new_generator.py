#!/usr/bin/env python3

import argparse
import sys
import subprocess
import logging
import os
import configparser


def script(args: argparse.Namespace, logger: logging.Logger, shell: callable) -> int:
    # Save args into config
    PATH_TO_NEW_TEST = os.path.join(
        os.path.dirname(os.path.abspath(__file__)), args.directory, args.test_name
    )
    logger.debug(f"DIR_PATH: {PATH_TO_NEW_TEST}")

    os.makedirs(PATH_TO_NEW_TEST, exist_ok=args.overwrite)

    # Write important args into config
    with open(os.path.join(PATH_TO_NEW_TEST, args.config), mode="w") as config_file:
        config = configparser.ConfigParser()
        config["file_names"] = {
            "test_name": args.test_name,
            "generator": args.generator,
            "expected": args.expected,
            "actual": args.actual,
            "module": args.module,
            "testbench": args.testbench,
        }
        config.write(config_file)

    with open(
        os.path.join(PATH_TO_NEW_TEST, args.generator), mode="w"
    ) as generator_file:
        generator_file.write(args.template)

    TEST_FILE_PATH = os.path.join(
        os.path.dirname(os.path.abspath(__file__)), args.test_file
    )
    logger.info(f"Appending to {TEST_FILE_PATH} with pytest function")
    with open(TEST_FILE_PATH, mode="a") as test_file:
        test_file.write(
            f"\n    def test_{args.test_name}(self, ()):\n        self.run_test(\"{args.test_name}\")\n"
        )

    logger.warn(
        f"Setup complete, replace content of {str(os.path.join(PATH_TO_NEW_TEST, args.generator))} with your python generator function"
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)

    # Positional arguments
    parser.add_argument(
        "test_name",
        type=str,
        help="Test directory name, e.g. circle_lines",
    )

    # Optional arguments
    parser.add_argument(
        "-v", "--verbose", action="count", default=0, help="Verbosity level"
    )
    parser.add_argument(
        "-o",
        "--overwrite",
        action="store_true",
        help="Overwrite existing files",
        default=False,
    )
    # WARNING: must come after "test_name" arg
    parser.add_argument(
        "--template",
        type=str,
        help="Template generator function",
        default=f"def {parser.parse_args().test_name}(a, b, c, d) -> tuple[int, int, int, int]:\n  yield(a, b)\n  yield(c, d)",
    )
    parser.add_argument(
        "-d",
        "--directory",
        type=str,
        help="Directory to make test in",
        default="data/generator/",
    )
    parser.add_argument(
        "--generator", type=str, help="Generator filename", default="generator.py"
    )
    parser.add_argument(
        "--expected", type=str, help="Expected output filename", default="expected.csv"
    )
    parser.add_argument(
        "--actual", type=str, help="Actual output filename", default="actual.csv"
    )
    parser.add_argument(
        "--module", type=str, help="Module filename", default="module.sv"
    )
    parser.add_argument(
        "--testbench", type=str, help="Testbench filename", default="testbench.sv"
    )
    parser.add_argument(
        "--config", type=str, help="Config filename", default="config.ini"
    )
    parser.add_argument(
        "--test_file", type=str, help="Filename of pytest", default="test_generator.py"
    )

    parser_args = parser.parse_args()

    logging.basicConfig(
        format="%(levelname)-8s [%(filename)s:%(lineno)d] %(message)s",
        datefmt="%Y-%m-%d:%H:%M:%S",
    )

    logger = logging.getLogger(__name__)

    logger.setLevel(max(40 - 10 * parser_args.verbose, 10))

    def shell(
        command: str,
        *args,
        shell: bool = True,  # Run the command in a shell
        check: bool = True,  # Ensure that the command executed successfully
        text: bool = True,  # Return stdout and stderr as strings instead of bytes
        capture_output: bool = True,  # Capture stdout and stderr
        **kwargs,
    ) -> subprocess.CompletedProcess:
        if parser_args.verbose >= 2:
            logger.info(
                f"Shell called at [{sys.argv[0]}:{sys._getframe().f_back.f_lineno}] with {command}"
            )
        return subprocess.run(
            command,
            *args,
            shell=shell,
            check=check,
            text=text,
            capture_output=capture_output,
            **kwargs,
        )

    logger.info(f"Running script: {sys.argv[0]} with args: {vars(parser_args)}")

    sys.exit(script(parser_args, logger, shell))
