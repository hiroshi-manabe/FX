#!/usr/bin/env python3
from configparser import ConfigParser
from collections import defaultdict
import sys
import os
import argparse
import csv
import re

def main(window_time, r_squared_value, start_week, end_week, debug):
    cfg = ConfigParser()
    cfg.read("config.ini")
    currency = cfg.get("settings", "currency_pair")

    if start_week is None or end_week is None:
        print(f"Usage: {sys.argv[0]} <start week> <end week>")
        sys.exit(-1)

    test_files = []
    for file in os.listdir(f"{currency}/weekly_past_data"):
        if file.startswith("week_") and file.endswith(".csv"):
            week_num = int(re.search(r"week_(\d{3})", file).group(1))
            if start_week <= week_num <= end_week:
                test_files.append((week_num, os.path.join(f"{currency}/weekly_past_data", file)))

    # Sort the list based on week numbers
    test_files.sort()

    past_width = window_time
    future_width = window_time // 4

    with open(f"{currency}/past_data.txt", "w") as fh_out_result:
        week_num = 1
        debug_file_counter = 1
        for _, test_file in test_files:
            print(test_file)
            fh_out_result.write(f"week {week_num}\n")
            week_num += 1

            data = []
            with open(test_file, "r") as fh:
                for line in csv.reader(fh):
                    line[0] = int(line[0])
                    data.append(line)

            prev_time = 0

            for i in range(len(data)):
                future_data = data[i][5].split("/")
                coeffs_data = data[i][6].split("/")

                record = None
                coeffs_record = None
                for item in future_data:
                    if item.startswith(f"{future_width}:"):
                        record = item
                        break
                
                for item in coeffs_data:
                    if item.startswith(f"{window_time}:"):
                        coeffs_record = item
                        break

                if record is not None and coeffs_record is not None:
                    buy_profit, end_time_buy, sell_profit, end_time_sell = map(float, record.split(":")[1:])
                    coeffs = list(map(float, coeffs_record.split(":")[1:4]))
                    fit = float(coeffs_record.split(":")[4])

                    if abs(coeffs[0]) < 3 and fit > r_squared_value and data[i][0] > prev_time + past_width + future_width:
                        j = i
                        while data[j][0] >= data[i][0] - past_width and j > 0:
                            j -= 1
                        j += 1

                        if i == j or past_width / (i - j) > 250:
                            continue

                        if debug:
                            temp_file = f"temp/{debug_file_counter:03d}.csv"
                            with open(temp_file, "w") as temp_csv:
                                temp_csv_writer = csv.writer(temp_csv)
                                for row in data[j:i+future_width+1]:
                                    temp_csv_writer.writerow([row[0], row[1]])
                            debug_file_counter += 1

                        fh_out_result.write(f"{coeffs[1]},{coeffs[2]},{int(buy_profit)},{int(sell_profit)}\n")
                        prev_time = data[i][0]
                            
if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--window_time", type=int, default=120000, help="window time value")
    parser.add_argument("--r_squared_value", type=float, default=0.94, help="r squared value")
    parser.add_argument("start_week", type=int, nargs='?', default=None, help="start week")
    parser.add_argument("end_week", type=int, nargs='?', default=None, help="end week")
    parser.add_argument("--debug", action="store_true", help="write debug files to temp directory")
    args = parser.parse_args()
    main(args.window_time, args.r_squared_value, args.start_week, args.end_week, args.debug)
