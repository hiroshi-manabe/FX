#!/usr/bin/env python3
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

def load_past_data(filename, start_train_week, end_train_week, start_dev_week, end_dev_week):
    with open(filename, 'r') as f:
        lines = f.readlines()
    
    data = {}
    current_week = 0
    for line in lines:
        if "week" in line:
            current_week = int(line.strip().split(" ")[1])
            data[current_week] = []
        else:
            data[current_week].append([float(x) for x in line.strip().split(',')])
    
    if end_train_week > max(data.keys()) or end_dev_week > max(data.keys()):
        raise ValueError("Specified week range exceeds the total number of weeks in the data.")

    train_data = []
    for week in range(start_train_week, end_train_week + 1):
        train_data.extend(data[week])

    dev_data = []
    for week in range(start_dev_week, end_dev_week + 1):
        dev_data.extend(data[week])

    return train_data, dev_data

def process_matching_points(train_data, dev_data, k, threshold):
    profit_sum = 0
    trade_count = 0
    for row in dev_data:
        first_coef, second_coef, buy_result, sell_result = row
        
        knn_buy = k_nearest_neighbors("buy", first_coef, second_coef, train_data, k=k, threshold=threshold)
        knn_sell = k_nearest_neighbors("sell", first_coef, second_coef, train_data, k=k, threshold=threshold)

        if knn_buy == "buy":
            action = "買い"
        elif knn_sell == "sell":
            action = "売り"
        else:
            action = "パス"
        
        print(f"1次係数: {first_coef}, 2次係数: {second_coef}, アクション: {action}")

        if action != "パス":
            profit = buy_result if action == "buy" else sell_result
            print(f"利益: {profit}")
            profit_sum += profit
            trade_count += 1

    if trade_count > 0:
        avr = profit_sum / trade_count
        print(f"合計利益: {profit_sum} 取引回数: {trade_count} 平均利益: {avr}")
    else:
        print("取引なし")


def k_nearest_neighbors(action, first_coef, second_coef, train_data, k=8, threshold=5):
    # Calculate the distances between the given data point and all past data points
    distances = []
    for i, past_point in enumerate(train_data):
        distance = (past_point[0] - first_coef) ** 2 + (past_point[1] - second_coef) ** 2
        distances.append((distance, i))

    # Find the k nearest neighbors
    distances.sort(key=lambda x: x[0])
    nearest_neighbors = distances[:k]

    # Count the number of points with a value greater than +20 and less than or equal to -20
    greater_than_20 = 0
    less_than_minus_20 = 0
    for _, neighbor_index in nearest_neighbors:
        value = train_data[neighbor_index][2 if action == "buy" else 3]  # Use the appropriate column for buy/sell results
        if value >= 20:
            greater_than_20 += 1
        elif value <= -20:
            less_than_minus_20 += 1

    if greater_than_20 - less_than_minus_20 >= threshold:
        return action
    else:
        return "pass"
        
def main(start_train_week, end_train_week, start_dev_week, end_dev_week, k_value=8, threshold_value=5):
    config = read_config("config.ini")
    currency_pair = find_currency_pair(config)
    
    if currency_pair is not None:
        file_path = f"{currency_pair}/past_data.txt"
        train_data, dev_data = load_past_data(file_path, start_train_week, end_train_week, start_dev_week, end_dev_week)
        
    process_matching_points(train_data, dev_data, k_value, threshold_value)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Process trading data")
    parser.add_argument("start_train_week", type=int, help="Start train week")
    parser.add_argument("end_train_week", type=int, help="End train week")
    parser.add_argument("start_dev_week", type=int, help="Start dev week")
    parser.add_argument("end_dev_week", type=int, help="End dev week")
    parser.add_argument("--k_value", type=int, default=8, help="k value for k-NN algorithm")
    parser.add_argument("--threshold_value", type=int, default=5, help="Threshold value for buy/sell decision")
    args = parser.parse_args()

    main(args.start_train_week, args.end_train_week, args.start_dev_week, args.end_dev_week, args.k_value, args.threshold_value)

