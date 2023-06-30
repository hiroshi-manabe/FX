#!/usr/bin/env python3
import argparse
import concurrent.futures
from concurrent.futures import ProcessPoolExecutor, as_completed
import configparser
import ctypes
import glob
import logging
import math
import os
import sys

libknn = ctypes.CDLL("./libknn.dylib")

libknn.k_nearest_neighbors.argtypes = [
    ctypes.c_double,
    ctypes.c_double,
    ctypes.POINTER(ctypes.c_double),
    ctypes.c_int,
    ctypes.c_int,
    ctypes.POINTER(ctypes.c_int),
]
libknn.k_nearest_neighbors.restype = None


def setup_logger(output_file=None):
    logger = logging.getLogger("trading")
    logger.setLevel(logging.INFO)

    formatter = logging.Formatter("%(message)s")

    if output_file:
        file_handler = logging.FileHandler(output_file)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    else:
        stream_handler = logging.StreamHandler(sys.stdout)
        stream_handler.setFormatter(formatter)
        logger.addHandler(stream_handler)

    return logger


def read_config(file_name):
    config = configparser.ConfigParser()
    config.read(file_name)
    return config


def find_currency_pair(config):
    try:
        return config.get("settings", "currency_pair")
    except (configparser.NoSectionError, configparser.NoOptionError):
        print("Currency pair not found in config file")
        return None


def compute_mean_std(train_data):
    mean_first_coef = sum(row[1] for row in train_data) / len(train_data)
    mean_second_coef = sum(row[2] for row in train_data) / len(train_data)
    
    std_first_coef = (sum((row[1] - mean_first_coef) ** 2 for row in train_data) / len(train_data)) ** 0.5
    std_second_coef = (sum((row[2] - mean_second_coef) ** 2 for row in train_data) / len(train_data)) ** 0.5
    
    return mean_first_coef, std_first_coef, mean_second_coef, std_second_coef


def normalize_data(data, mean_first_coef, std_first_coef, mean_second_coef, std_second_coef):
    normalized_data = []
    for row in data:
        normalized_first_coef = (row[1] - mean_first_coef) / std_first_coef
        normalized_second_coef = (row[2] - mean_second_coef) / std_second_coef
        normalized_row = [row[0], normalized_first_coef, normalized_second_coef, row[3], row[4]]
        normalized_data.append(normalized_row)
    return normalized_data


def process_matching_points(logger, train_data, dev_data, min_k, max_k):
    if len(train_data) < max_k:
        return
    
    profit_sum = 0
    trade_count = 0
    threshold = 20
    
    for row in dev_data:
        timestamp, first_coef, second_coef, buy_result, sell_result = row
        knn_results = []
        # Create a preallocated array of the appropriate size
        output_array = (ctypes.c_int * max_k)()
        k_nearest_neighbors(first_coef, second_coef, train_data, output_array, k=max_k)

        avr_x = sum(train_data[output_array[i]][1] for i in range(max_k)) / max_k
        avr_y = sum(train_data[output_array[i]][2] for i in range(max_k)) / max_k
        distance_to_center = math.sqrt((first_coef - avr_x) ** 2 + (second_coef - avr_y) ** 2)
        radius = math.sqrt((first_coef - train_data[output_array[max_k - 1]][1]) ** 2 + (second_coef - train_data[output_array[max_k - 1]][2]) ** 2)
        if distance_to_center > radius / 2:
            continue

        k_values = range(min_k, max_k + 1)
        results = [[], []]

        threshold = 20

        for col_offset in range(2):
            plus_minus = 0
            for i in range(max_k):
                col_index = 3 + col_offset
                pl = train_data[output_array[i]][col_index]
                if pl >= threshold:
                    plus_minus += 1
                elif pl <= -threshold:
                    plus_minus -= 1
                if i >= min_k - 1:
                    results[col_offset].append(plus_minus)

        final_str = ":".join(f"{k}/{buy}/{sell}" for k, buy, sell in zip(k_values, results[0], results[1]))

        logger.info(f"{int(timestamp)},{first_coef},{second_coef},{final_str},{int(buy_result)},{int(sell_result)}")


def k_nearest_neighbors(first_coef, second_coef, train_data, output_array, k=10):
    flattened_data = [value for sublist in train_data for value in sublist[1:3]]
    num_data_points = len(train_data)

    c_double_array = (ctypes.c_double * len(flattened_data))()
    for i, value in enumerate(flattened_data):
        c_double_array[i] = value

    libknn.k_nearest_neighbors(
        first_coef,
        second_coef,
        c_double_array,
        num_data_points,
        k,
        output_array,
    )
    return

    
def load_data_from_files(directory, start_week, end_week, window_time, r_squared_value):
    data = []
    for week in range(start_week, end_week + 1):
        file_path = os.path.join(directory, f"week_{week:03d}_*.csv")
        files = glob.glob(file_path)

        if not files:
            raise ValueError(f"No data file found for week {week}")
        if len(files) > 1:
            raise ValueError(f"Multiple files found for week {week}: {files}")

        with open(files[0], 'r') as f:
            lines = f.readlines()
            week_data = [list(map(float, line.strip().split(','))) for line in lines]
            filtered_week_data = [row[:1] + row[3:] for row in week_data if row[1] == window_time and row[2] == r_squared_value]
            data.extend(filtered_week_data)
    return data


def main(logger, start_train_week, end_train_week, start_dev_week, end_dev_week, k_value=8, threshold_value=5, window_time=60000, r_squared_value=0.95):
    config = read_config("config.ini")
    currency_pair = find_currency_pair(config)
    currency_pair_directory = os.path.join(currency_pair, "weekly_digest")

    if currency_pair is not None:
        train_data = load_data_from_files(currency_pair_directory, start_train_week, end_train_week, window_time, r_squared_value)
        dev_data = load_data_from_files(currency_pair_directory, start_dev_week, end_dev_week, window_time, r_squared_value)

        if len(train_data) < k_value:
            sys.exit(0)

        # Compute mean and standard deviation for the first and second coefficients in the training data
        mean_first_coef, std_first_coef, mean_second_coef, std_second_coef = compute_mean_std(train_data)
        if std_first_coef == 0 or std_second_coef == 0:
            sys.exit(0)
        
        # Normalize the first and second coefficients in the training and development data
        train_data = normalize_data(train_data, mean_first_coef, std_first_coef, mean_second_coef, std_second_coef)
        dev_data = normalize_data(dev_data, mean_first_coef, std_first_coef, mean_second_coef, std_second_coef)

    process_matching_points(logger, train_data, dev_data, k_value, threshold_value)


def process_params(params):
    start_train_week, end_train_week, start_dev_week, end_dev_week, k_value, threshold_value, window_time, r_squared_value, output_file = params
    logger = setup_logger(output_file)
    main(logger, start_train_week, end_train_week, start_dev_week, end_dev_week, k_value, threshold_value, window_time, r_squared_value)

    
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Process trading data")
    parser.add_argument("--stdin", action="store_true", help="Read parameters from standard input instead of a file")
    parser.add_argument("start_train_week", type=int, nargs="?", help="Start train week")
    parser.add_argument("end_train_week", type=int, nargs="?", help="End train week")
    parser.add_argument("start_dev_week", type=int, nargs="?", help="Start dev week")
    parser.add_argument("end_dev_week", type=int, nargs="?", help="End dev week")
    parser.add_argument("--min_k_value", type=int, default=5, nargs="?", help="Minimum k value for k-NN algorithm")
    parser.add_argument("--max_k_value", type=int, default=10, nargs="?", help="Maximum k value for k-NN algorithm")
    parser.add_argument("--window_time", type=int, default=60000, nargs="?", help="Window time value for filtering data")
    parser.add_argument("--r_squared_value", type=float, default=0.95, nargs="?", help="R-squared value for filtering data")
    parser.add_argument("--num_processes", type=int, default=os.cpu_count(), nargs="?", help="Number of parallel processes to use")
    args = parser.parse_args()

    if args.stdin:
        params_list = []
        for line in sys.stdin:
            values = line.strip().split(",")
            start_train_week, end_train_week, start_dev_week, end_dev_week = map(int, values[:4])
            min_k_value, max_k_value, window_time = map(int, values[4:7])
            r_squared_value = float(values[7])
            output_file = values[8]
            params_list.append((start_train_week, end_train_week, start_dev_week, end_dev_week, min_k_value, max_k_value, window_time, r_squared_value, output_file))

        with concurrent.futures.ProcessPoolExecutor(max_workers=args.num_processes) as executor:
            executor.map(process_params, params_list)
    else:
        logger = setup_logger()
        main(logger, args.start_train_week, args.end_train_week, args.start_dev_week, args.end_dev_week, args.min_k_value, args.max_k_value, args.window_time, args.r_squared_value)
