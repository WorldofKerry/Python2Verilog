import os
import csv
import configparser
import csv
import pandas as pd
import argparse


def count_lines_in_csv(directory: str, file: str) -> int:
    """
    Gets the number of lines in a csv file
    """
    csv_path = os.path.join(directory, file)
    if not os.path.isfile(csv_path):
        print(f"No 'actual.csv' found in {directory}")
        return

    with open(csv_path, "r") as csv_file:
        csv_reader = csv.reader(csv_file)
        line_count = sum(1 for _ in csv_reader)

    return line_count


def get_expected_and_actual_lines(directory: str) -> dict:
    """
    Gets the number of lines in actual and expected files
    """
    config = configparser.ConfigParser(allow_no_value=True)
    config.read(os.path.join(directory, "config.ini"))
    FILE_NAMES = config["file_names"]
    return {
        "Test Case": os.path.basename(directory),
        "Verilog Clock Cycles": count_lines_in_csv(directory, FILE_NAMES["actual"]),
        "Python Yield Iterations": count_lines_in_csv(
            directory, FILE_NAMES["expected"]
        ),
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawTextHelpFormatter
    )
    parser.add_argument("directory", type=str, help="Directory to collect stats on")
    args = parser.parse_args()

    SCRIPT_DIR = os.path.abspath(args.directory)
    STATS_CSV = os.path.join(SCRIPT_DIR, "stats.csv")

    # Iterate over the subdirectories in the script directory
    tests = []
    for root, dirs, files in os.walk(SCRIPT_DIR):
        for directory in dirs:
            directory_path = os.path.join(root, directory)
            tests.append(get_expected_and_actual_lines(directory_path))
    tests = sorted(tests, key=lambda e: e["Test Case"])

    with open(STATS_CSV, mode="w") as stats_csv:
        writer = csv.DictWriter(stats_csv, fieldnames=tests[0].keys())
        writer.writeheader()
        writer.writerows(tests)

    df = pd.read_csv(STATS_CSV)
    print(df.to_markdown(index=False))
