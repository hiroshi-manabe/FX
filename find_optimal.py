#!/usr/bin/env python3
import argparse
import configparser
import csv
import numpy as np
import os

def parse_arguments():
    parser = argparse.ArgumentParser()
    parser.add_argument("last_week", type=int, help="The 'last_week' command-line argument.")
    return parser.parse_args()

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

def simulate_log_return(mu, sigma, n_simulations=100000):
    return np.random.normal(mu, sigma, n_simulations)

def calculate_log_return(f, outcomes):
    return np.mean(np.log((1 - f) + f * outcomes))

def binary_search(mu, sigma, tol=1e-6, max_iter=100):
    outcomes = simulate_log_return(mu, sigma)
    lower, upper = 0.0, 1.0
    for _ in range(max_iter):
        mid_f = (lower + upper) / 2
        left_f = (lower + mid_f) / 2
        right_f = (mid_f + upper) / 2

        left_log_return = calculate_log_return(left_f, outcomes)
        mid_log_return = calculate_log_return(mid_f, outcomes)
        right_log_return = calculate_log_return(right_f, outcomes)

        if np.abs(left_log_return - right_log_return) < tol:
            return mid_f

        if left_log_return > mid_log_return:
            upper = mid_f
        elif right_log_return > mid_log_return:
            lower = mid_f
        else:
            lower, upper = left_f, right_f

    return (lower + upper) / 2

def process_input_line(input_line):
    data = input_line.split(',')
    label = data[0]
    trials, avg_pl, std_dev = map(float, data[1:])

    if trials < 30 or avg_pl < 30 or std_dev == 0:
        return None

    desired_std_dev = 0.15
    scaling_factor = desired_std_dev / std_dev

    initial_principal = 1

    adjusted_avg_pl = avg_pl * scaling_factor
    adjusted_std_dev = std_dev * scaling_factor

    final_expected_avg_value = initial_principal + adjusted_avg_pl
    optimal_f = binary_search(final_expected_avg_value, adjusted_std_dev)
    final_f = optimal_f * scaling_factor

    final_mean = initial_principal + avg_pl * final_f
    final_std_dev = std_dev * final_f

    outcomes = simulate_log_return(final_mean, final_std_dev)
    expected_log_value = calculate_log_return(1, outcomes)

    return label, expected_log_value * trials, final_f

config = read_config("config.ini")
currency_pair = find_currency_pair(config)
window_times = config.get("settings", "window_times")
window_times_list = [int(x) for x in window_times.split(",")]

args = parse_arguments()
last_week = args.last_week

root_directory = f"{currency_pair}/results_{last_week:02d}"
overall_result_for_current_training_weeks = 0

for window_time in window_times_list:
    input_file_path = f"{root_directory}/{window_time}.csv"

    if not os.path.exists(input_file_path):
        continue

    with open(input_file_path, 'r') as input_file:
        csv_reader = csv.reader(input_file)
        results = []

        for input_line in csv_reader:
            result = process_input_line(','.join(input_line))
            if result is not None:
                results.append(result)

        if results:
            best_label_for_current_window_time, best_result_for_current_window_time, best_final_f = max(results, key=lambda x: x[1])
            overall_result_for_current_training_weeks += best_result_for_current_window_time
            print(f"Best result for last_week {last_week}, window_time {window_time}: Label {best_label_for_current_window_time}, Value {best_result_for_current_window_time}, Final_f {best_final_f}")

print(f"Result for last_week {last_week}: {overall_result_for_current_training_weeks}")
