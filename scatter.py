import re
import argparse
import configparser
import matplotlib.pyplot as plt

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

def process_line(line, args, data_a, data_b, data_c):
    items = line.strip().split(',')
    if len(items) == 4:
        try:
            a, b, c, d = map(float, items)
            if a < -0.01 or a > 0.01:
                return
            if args.trade_type == "buy":
                data_a.append(a)
                data_b.append(b)
                data_c.append(c)
            else:
                data_a.append(a)
                data_b.append(b)
                data_c.append(d)
        except ValueError:
            pass

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("trade_type", choices=["buy", "sell"], help="Select trade type: buy or sell")
    parser.add_argument("train_start_week", type=int, help="Training data start week")
    parser.add_argument("train_end_week", type=int, help="Training data end week")
    parser.add_argument("dev_start_week", type=int, help="Development data start week")
    parser.add_argument("dev_end_week", type=int, help="Development data end week")
    args = parser.parse_args()

    config = read_config("config.ini")
    currency_pair = find_currency_pair(config)

    current_week = 1
    is_data_week = False
    with open(f'{currency_pair}/past_data.txt', 'r') as file:
        for line in file:
            if line.startswith("week"):
                current_week = int(line.split()[1])
                is_data_week = args.train_start_week <= current_week <= args.train_end_week or \
                               args.dev_start_week <= current_week <= args.dev_end_week
            elif is_data_week:
                process_line(line, args, data_a, data_b, data_c)

    marker_sizes = [1 if args.train_start_week <= i <= args.train_end_week else 10 for i in range(len(data_a))]

    for a, b, c, size in zip(data_a, data_b, data_c, marker_sizes):
        if c >= 20:
            color = 'blue'
        elif c <= -20:
            color = 'red'
        else:
            color = 'black'
        plt.scatter(a, b, c=color, s=size)

    plt.xlabel('X-axis (a)')
    plt.ylabel('Y-axis (b)')
    plt.title(f'Scatter Plot with Color-Coded Points based on {args.trade_type} profit value')
    plt.show()
