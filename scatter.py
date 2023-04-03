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

def process_line(line, week, args, train_start, train_end, dev_start, dev_end):
    items = line.strip().split(',')
    if len(items) == 4:
        try:
            a, b, c, d = map(float, items)
            if a < -0.01 or a > 0.01:
                return
            if train_start <= week <= train_end and args.trade_type == "buy":
                data_a.append(a)
                data_b.append(b)
                data_c.append((c, "train"))
            elif dev_start <= week <= dev_end and args.trade_type == "buy":
                data_a.append(a)
                data_b.append(b)
                data_c.append((c, "dev"))
            elif train_start <= week <= train_end and args.trade_type == "sell":
                data_a.append(a)
                data_b.append(b)
                data_c.append((d, "train"))
            elif dev_start <= week <= dev_end and args.trade_type == "sell":
                data_a.append(a)
                data_b.append(b)
                data_c.append((d, "dev"))
        except ValueError:
            return

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("trade_type", choices=["buy", "sell"], help="Select trade type: buy or sell")
    parser.add_argument("train_start", type=int, help="Training data start week")
    parser.add_argument("train_end", type=int, help="Training data end week")
    parser.add_argument("dev_start", type=int, help="Development data start week")
    parser.add_argument("dev_end", type=int, help="Development data end week")
    args = parser.parse_args()

    config = read_config("config.ini")
    currency_pair = find_currency_pair(config)
    
    with open(f'{currency_pair}/past_data.txt', 'r') as file:
        week = 0
        for line in file:
            if "week" in line:
                week = int(re.findall(r'\d+', line)[0])
                continue
            process_line(line, week, args, args.train_start, args.train_end, args.dev_start, args.dev_end)

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
