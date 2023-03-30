import os
import glob
import configparser
import sys

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

def load_past_data(currency):
    file_path = f"{currency}/past_data.txt"
    data = []

    with open(file_path, "r") as file:
        for line in file:
            line = line.strip()
            if not line.startswith("week"):
                coeffs = list(map(float, line.split(',')))
                data.append(coeffs)

    return data

def load_data(currency_pair, start_week, end_week):
    data = []
    base_dir = f"{currency_pair}/weekly_past_data/"

    for week in range(start_week, end_week + 1):
        filename = f"{base_dir}week_{week:03d}_*.csv"
        file_list = glob.glob(filename)
        if len(file_list) == 1:
            file_path = file_list[0]
            with open(file_path, "r") as file:
                lines = file.readlines()

                for line in lines:
                    columns = line.strip().split(",")
                    timestamp = int(columns[0])
                    ask = float(columns[1])

                    coef_str = columns[-1].split(":")
                    zero_coef = float(coef_str[1])
                    first_coef = float(coef_str[2])
                    second_coef = float(coef_str[3])
                    r_squared = float(coef_str[4])

                    data.append((week, timestamp, ask, zero_coef, first_coef, second_coef, r_squared))
        else:
            print(f"File not found or multiple files found for week {week}")

    return data

def find_matching_points(data):
    matching_indices = []
    last_matched_timestamp = None
    last_matched_week = None

    for i, row in enumerate(data):
        current_week, current_timestamp, _, zero_coef, first_coef, second_coef, r_squared = row

        if abs(zero_coef) < 3 and r_squared >= 0.94:
            # Check if there are enough data points
            past_data_points = [dp for dp in data[max(0, i - 120000 // 250):i] if dp[1] >= current_timestamp - 120000]

            if len(past_data_points) >= (120000 / 250):
                # Check if 120 seconds have passed since the last match
                if last_matched_timestamp is None or current_week != last_matched_week or (current_timestamp - last_matched_timestamp) >= 120000:
                    matching_indices.append(i)
                    last_matched_timestamp = current_timestamp
                    last_matched_week = current_week

    return matching_indices

def k_nearest_neighbors(index, data, past_data, k=8):
    # Calculate the distances between the given data point and all past data points
    distances = []
    for i, past_point in enumerate(past_data):
        distance = sum([(data[index][j + 4] - past_point[j]) ** 2 for j in range(2)])  # 3 and 4 are the relevant columns for data
        distances.append((distance, i))

    # Find the k nearest neighbors
    distances.sort(key=lambda x: x[0])
    nearest_neighbors = distances[:k]

    # Count the number of points with a value greater than +20 and less than or equal to -20
    greater_than_20 = 0
    less_than_minus_20 = 0
    for _, neighbor_index in nearest_neighbors:
        value = past_data[neighbor_index][2]  # The 'result after 30 seconds' column
        if value >= 20:
            greater_than_20 += 1
        elif value <= -20:
            less_than_minus_20 += 1

    # Decide whether to buy, sell, or pass based on the counts
    if greater_than_20 - less_than_minus_20 >= 5:
        return "buy"
    elif less_than_minus_20 - greater_than_20 >= 5:
        return "sell"
    else:
        return "pass"

def process_trade(action, index, data):
    window_size = 100
    window_time = 15 * 1000
    initial_ask = data[index][2]
    profit = 0
    no_stop_time = 30 * 1000  # 30 seconds in milliseconds

    def find_previous_data_point(i, data):
        for j in range(i - 1, 0, -1):
            if data[i][1] - data[j][1] >= window_time:
                return j
        return None
    
    # Skip the first 30 seconds
    i = index
    while i < len(data) - window_size:
        current_timestamp = data[i][1]
        initial_timestamp = data[index][1]

        if current_timestamp - initial_timestamp < no_stop_time:
            i += 1
            continue

        prev_index = find_previous_data_point(i, data)
        current_ask = data[i][2]
        previous_ask = data[prev_index][2]

        if action == "buy" and current_ask < previous_ask:
            profit = data[i][2] - initial_ask
            break
        elif action == "sell" and current_ask > previous_ask:
            profit = initial_ask - data[i][2]
            break

        i += 1

    return profit

def process_matching_points(matching_indices, data, past_data):
    profit_sum = 0
    trade_count = 0
    for index in matching_indices:
        week, timestamp, ask, zero_coef, first_coef, second_coef, r_squared = data[index]
        
        knn_result = k_nearest_neighbors(index, data, past_data)
        if knn_result == "buy":
            action = "買い"
        elif knn_result == "sell":
            action = "売り"
        else:
            action = "パス"
        
        print(f"週: {week}, タイムスタンプ: {timestamp}, アクション: {action}")
        
        if knn_result == "pass":
            continue
        
        profit = process_trade(knn_result, index, data)
        print(f"利益: {profit}")
        profit_sum += profit
        trade_count += 1

    if trade_count > 0:
        avr = profit_sum / trade_count
        print(f"合計利益: {profit_sum} 取引回数: {trade_count} 平均利益: {avr}")
    else:
        print("取引なし")

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python load_data.py <start_week> <end_week>")
        sys.exit(1)

    start_week = int(sys.argv[1])
    end_week = int(sys.argv[2])

    config = read_config("config.ini")
    currency_pair = find_currency_pair(config)

    if currency_pair is not None:
        past_data = load_past_data(currency_pair)
        data = load_data(currency_pair, start_week, end_week)

    else:
        print("No currency pair found in config file")

    matching_indices = find_matching_points(data)
    process_matching_points(matching_indices, data, past_data)
