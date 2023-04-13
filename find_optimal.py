#!/usr/bin/env python3
import numpy as np

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

input_line = input().strip()
data = input_line.split(',')
label = data[0]
trials, avg_pl, std_dev = map(float, data[1:])

desired_std_dev = 0.2
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

print("Optimal betting fraction:", final_f)
print("Expected log value of the result:", expected_log_value)
