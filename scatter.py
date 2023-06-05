import re
import argparse
import configparser
import matplotlib.pyplot as plt
import glob
import numpy as np
import os
import pandas as pd

data_a = []
data_b = []
data_c = []

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

def process_file(file_name, week, args):
    data = pd.read_csv(file_name)
    prev_time = 0
    for _, row in data.iterrows():
        if row[1] != args.window_time or row[2] < args.r_squared_value or row[0] == prev_time:
            continue

        a = row[3]
        b = row[4]
        profit = row[5] if args.trade_type == "buy" else row[6]
        data_type = "train" if args.train_start <= week <= args.train_end else "dev"

        data_a.append(a)
        data_b.append(b)
        data_c.append((profit, data_type))
        prev_time = row[0]

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("trade_type", choices=["buy", "sell"], help="Select trade type: buy or sell")
    parser.add_argument("window_time", type=int, help="Window time in milliseconds")
    parser.add_argument("r_squared_value", type=float, help="Minimum determination coefficient")
    parser.add_argument("train_start", type=int, help="Training data start week")
    parser.add_argument("train_end", type=int, help="Training data end week")
    parser.add_argument("dev_start", type=int, help="Development data start week")
    parser.add_argument("dev_end", type=int, help="Development data end week")
    args = parser.parse_args()

    config = read_config("config.ini")
    currency_pair = find_currency_pair(config)

    for week in range(args.train_start, args.train_end + 1):
        files = glob.glob(f'{currency_pair}/weekly_digest/week_{week:03d}_*.csv')
        if len(files) != 1:
            raise ValueError(f'Expected exactly one file for week {week}, but found {len(files)}')
        process_file(files[0], week, args)

    for week in range(args.dev_start, args.dev_end + 1):
        files = glob.glob(f'{currency_pair}/weekly_digest/week_{week:03d}_*.csv')
        if len(files) != 1:
            raise ValueError(f'Expected exactly one file for week {week}, but found {len(files)}')
        process_file(files[0], week, args)

    data_a = np.array(data_a)
    data_b = np.array(data_b)

    train_indices = [i for i, c_data in enumerate(data_c) if c_data[1] == 'train']
    print(f"{len(train_indices)=}")

    mean_a, std_a = np.mean(data_a[train_indices]), np.std(data_a[train_indices])
    mean_b, std_b = np.mean(data_b[train_indices]), np.std(data_b[train_indices])

    data_a = (data_a - mean_a) / std_a
    data_b = (data_b - mean_b) / std_b
    print(f"{mean_a=}, {std_a=}, {mean_b=}, {std_b=}")

    for a, b, c_data in zip(data_a, data_b, data_c):
        c, data_type = c_data
        if c >= 20:
            color = 'blue'
        elif c <= -20:
            color = 'red'
        else:
            color = 'black'
        size = 20 if data_type == "dev" else 1
        plt.scatter(a, b, c=color, s=size)

    plt.xlabel('X-axis (a)')
    plt.ylabel('Y-axis (b)')
    plt.title(f'Scatter Plot with Color-Coded Points based on {args.trade_type} profit value')
    plt.show()
