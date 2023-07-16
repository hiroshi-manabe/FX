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


config = read_config("config.ini")
currency_pair = config.get("settings", "currency_pair")
window_times = config.get("settings", "window_times")
window_times_list = [int(x) for x in window_times.split(",")]
min_profit = int(config.get("settings", "min_profit"))
k_value = int(config.get("settings", "k_value"))

args = parse_arguments()
last_week = args.last_week

root_directory = f"{currency_pair}/results_{last_week:02d}"

for window_time in window_times_list:
    input_file_path = f"{root_directory}/{window_time}.csv"

    if not os.path.exists(input_file_path):
        continue

    with open(input_file_path, 'r') as input_file:
        csv_reader = csv.reader(input_file)
        (prev_r_squared, prev_k) = (None, None)
        for input_line in csv_reader:
            label = input_line[0]
            t = label.split('/')
            r_squared = t[0]
            k, threshold = map(int, t[1:3])
            trials, avg_pl, std_dev = map(float, input_line[1:])
            
            if (not (r_squared == prev_r_squared and
                     k == prev_k) and
                k == k_value and
                (trials > 1 and
                  avg_pl >= min_profit)):
                print(",".join(str(x) for x in (window_time, r_squared, k, threshold)))
                (prev_r_squared, prev_k) = (r_squared, k)
