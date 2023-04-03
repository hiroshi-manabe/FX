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

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("trade_type", choices=["buy", "sell"], help="Select trade type: buy or sell")
    args = parser.parse_args()

    config = read_config("config.ini")
    currency_pair = find_currency_pair(config)
    
    with open(f'{currency_pair}/past_data.txt', 'r') as file:
        for line in file:
            items = line.strip().split(',')
            if len(items) == 4:
                try:
                    a, b, c, d = map(float, items)
                    if a < -0.01 or a > 0.01:
                        continue
                    if args.trade_type == "buy":
                        data_a.append(a)
                        data_b.append(b)
                        data_c.append(c)
                    else:
                        data_a.append(a)
                        data_b.append(b)
                        data_c.append(d)
                except ValueError:
                    continue

    for a, b, c in zip(data_a, data_b, data_c):
        if c >= 20:
            color = 'blue'
        elif c <= -20:
            color = 'red'
        else:
            color = 'black'
        plt.scatter(a, b, c=color, s=1)

    plt.xlabel('X-axis (a)')
    plt.ylabel('Y-axis (b)')
    plt.title(f'Scatter Plot with Color-Coded Points based on {args.trade_type} profit value')
    plt.show()
