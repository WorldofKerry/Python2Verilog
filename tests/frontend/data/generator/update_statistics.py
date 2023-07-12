import os
import csv
import configparser
import csv


def count_lines_in_csv(directory, file):
    csv_path = os.path.join(directory, file)
    if not os.path.isfile(csv_path):
        print(f"No 'actual.csv' found in {directory}")
        return

    with open(csv_path, "r") as csv_file:
        csv_reader = csv.reader(csv_file)
        line_count = sum(1 for _ in csv_reader)

    return line_count


def get_expected_and_actual_lines(directory):
    config = configparser.ConfigParser(allow_no_value=True)
    print(os.path.join(directory, "config.ini"))
    config.read(os.path.join(directory, "config.ini"))
    FILE_NAMES = config["file_names"]
    return {
        "test": os.path.basename(directory),
        "actual": count_lines_in_csv(directory, FILE_NAMES["actual"]),
        "expected": count_lines_in_csv(directory, FILE_NAMES["expected"]),
    }


# Get the directory where the script is located
script_directory = os.path.dirname(os.path.abspath(__file__))

# Iterate over the subdirectories in the script directory
tests = []
for root, dirs, files in os.walk(script_directory):
    for directory in dirs:
        directory_path = os.path.join(root, directory)
        tests.append(get_expected_and_actual_lines(directory_path))

with open(os.path.join(script_directory, "stats.csv"), mode="w") as stats_file:
    csv_writer = csv.writer(stats_file)
    for test in tests:
        csv_writer.writerow([test["test"], test["expected"], test["actual"]])
