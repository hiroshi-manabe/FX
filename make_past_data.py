#!/usr/bin/env python3
from configparser import ConfigParser
from collections import defaultdict
import sys
import os
import argparse
import csv
import re

def main(r_squared_values, start_week, end_week, debug):
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

    week_num = 1
    debug_file_counter = 1
    os.makedirs(f"{currency}/weekly_digest", exist_ok=True)

    for file in os.listdir(f"{currency}/weekly_digest"):
        if re.match(r"week_\d{3}_\d{8}\.csv", file):
            os.remove(os.path.join(f"{currency}/weekly_digest", file))
    
    for _, test_file in test_files:
        output_filename = os.path.basename(test_file)
        with open(f"{currency}/weekly_digest/{output_filename}", "w") as fh_out_result:
            print(test_file)
            week_num += 1

            data = []
            with open(test_file, "r") as fh:
                for line in csv.reader(fh):
                    line[0] = int(line[0])
                    data.append(line)

            prev_time_dict = defaultdict(lambda: defaultdict(int))

            for i in range(len(data)):
                future_data = data[i][5].split("/")
                coeffs_data = data[i][6].split("/")

                for record, coeffs_record in zip(future_data, coeffs_data):
                    future_width, buy_profit, end_time_buy, sell_profit, end_time_sell = map(float, record.split(":"))
                    future_width = int(future_width)
                    l = list(map(float, coeffs_record.split(":")))
                    past_width = int(l[0])
                    coeffs = l[1:4]
                    fit = l[4]

                    density_checked = False
                    density_ok = False
                    for r_squared_value in r_squared_values:
                        if abs(coeffs[0]) < 3 and fit > r_squared_value and data[i][0] > prev_time_dict[past_width][r_squared_value] + past_width + future_width:
                            if not density_checked:
                                density_checked = True
                                j = i
                                while data[j][0] >= data[i][0] - past_width and j > 0:
                                    j -= 1
                                j += 1

                                if i == j or past_width / (i - j) > 250:
                                    density_ok = False
                                    continue
                                else:
                                    density_ok = True
                            else:
                                if not density_ok:
                                    continue
                                

                            if debug:
                                temp_file = f"temp/{debug_file_counter:03d}.csv"
                                with open(temp_file, "w") as temp_csv:
                                    temp_csv_writer = csv.writer(temp_csv)
                                    for row in data[j:i+future_width+1]:
                                        temp_csv_writer.writerow([row[0], row[1]])
                                debug_file_counter += 1

                            fh_out_result.write(f"{data[i][0]},{past_width},{r_squared_value},{coeffs[1]},{coeffs[2]},{int(buy_profit)},{int(sell_profit)}\n")
                            prev_time_dict[past_width][r_squared_value] = data[i][0]

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--r_squared_values", type=float, nargs='+', default=[0.94], help="list of r squared values")
    parser.add_argument("start_week", type=int, nargs='?', default=None, help="start week")
    parser.add_argument("end_week", type=int, nargs='?', default=None, help="end week")
    parser.add_argument("--debug", action="store_true", help="write debug files to temp directory")
    args = parser.parse_args()
    main(args.r_squared_values, args.start_week, args.end_week, args.debug)
