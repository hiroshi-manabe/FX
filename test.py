import argparse
import configparser
import glob
import os
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

def load_past_data(currency_pair):
    file_path = f"{currency_pair}/past_data.txt"
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

def find_matching_points(data, r_squared_threshold=0.94, window_time=120000):
    matching_indices = []
    last_matched_timestamp = None
    last_matched_week = None

    for i, row in enumerate(data):
        current_week, current_timestamp, _, zero_coef, first_coef, second_coef, r_squared = row

        if abs(zero_coef) < 3 and r_squared >= r_squared_threshold:
            # Check if there are enough data points
            past_data_points = [dp for dp in data[max(0, i - window_time // 250):i] if dp[1] >= current_timestamp - window_time]

            if len(past_data_points) >= (window_time / 250):
                # Check if the window time have passed since the last match
                if last_matched_timestamp is None or current_week != last_matched_week or (current_timestamp - last_matched_timestamp) >= window_time:
                    matching_indices.append(i)
                    last_matched_timestamp = current_timestamp
                    last_matched_week = current_week

    return matching_indices

def k_nearest_neighbors(index, data, past_data, k=8, threshold=5):
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
        value = past_data[neighbor_index][2]  # The 'result' column
        if value >= 20:
            greater_than_20 += 1
        elif value <= -20:
            less_than_minus_20 += 1

    # Decide whether to buy, sell, or pass based on the counts
    if greater_than_20 - less_than_minus_20 >= threshold:
        return "buy"
    elif less_than_minus_20 - greater_than_20 >= threshold:
        return "sell"
    else:
        return "pass"

def process_trade(action, index, data, past_window_time):
    initial_ask = data[index][2]
    profit = 0

    def find_previous_data_point(i, data):
        for j in range(i - 1, 0, -1):
            if data[i][1] - data[j][1] >= past_window_time:
                return j
        return None
    
    i = index
    while i < len(data):
        current_timestamp = data[i][1]
        initial_timestamp = data[index][1]

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

def process_matching_points(matching_indices, data, past_data, window_time):
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

        past_window_time = window_time // 4
        profit = process_trade(knn_result, index, data, past_window_time)
        print(f"利益: {profit}")
        profit_sum += profit
        trade_count += 1

    if trade_count > 0:
        avr = profit_sum / trade_count
        print(f"合計利益: {profit_sum} 取引回数: {trade_count} 平均利益: {avr}")
    else:
        print("取引なし")

def main(start_week, end_week, k_value=8, threshold_value=5, r_squared_value=0.94, window_time=120000):

    config = read_config("config.ini")
    currency_pair = find_currency_pair(config)

    if currency_pair is not None:
        past_data = load_past_data(currency_pair)
        data = load_data(currency_pair, start_week, end_week)

    else:
        print("No currency pair found in config file")

    matching_indices = find_matching_points(data, r_squared_value)
    process_matching_points(matching_indices, data, past_data)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Process trading data")
    parser.add_argument("start_week", type=int, help="Start week")
    parser.add_argument("end_week", type=int, help="End week")
    parser.add_argument("--k_value", type=int, default=8, help="k value for k-NN algorithm")
    parser.add_argument("--threshold_value", type=int, default=5, help="Threshold value for buy/sell decision")
    parser.add_argument("--r_squared_value", type=float, default=0.94, help="R-squared threshold value for matching points")
    parser.add_argument("--window_time", type=int, default=120000, help="Window time in milliseconds")

    args = parser.parse_args()

    main(args.start_week, args.end_week, args.k_value, args.threshold_value, args.r_squared_value, window_time)

