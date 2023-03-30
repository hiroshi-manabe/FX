import re
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
    config = read_config("config.ini")
    currency_pair = find_currency_pair(config)
    with open(f'{currency_pair}/past_data.txt', 'r') as file:
        for line in file:
            items = line.strip().split(',')
            if len(items) == 3:
                try:
                    a, b, c = map(float, items)
                    if a < -0.01 or a > 0.01:
                        continue
                    data_a.append(a)
                    data_b.append(b)
                    data_c.append(c)
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
    plt.title('Scatter Plot with Color-Coded Points based on c value')
    plt.show()
