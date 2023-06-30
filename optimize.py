import numpy as np
from scipy.optimize import minimize

# Load the data
data = np.loadtxt('data.txt', delimiter='\t')

# Define the quadratic function
def quad_func(params, x):
    a, b, c = params
    return a*x**2 + b*x + c

# Define the objective function for optimization
def objective(params):
    curve_values = quad_func(params, data[:, 0])
    above_curve_indices = data[:, 1] > curve_values
    total = np.sum(data[above_curve_indices, 2])
    return -total  # We want to maximize this total, so return its negative for minimization

# Start with some random coefficients
params_initial = np.random.rand(3)

# Perform the optimization
result = minimize(objective, params_initial, method='nelder-mead')

# Print out the optimal parameters
print('Optimal parameters:', result.x)

# Compute and print the final total sum
final_curve_values = quad_func(result.x, data[:, 0])
final_above_curve_indices = data[:, 1] > final_curve_values
final_total = np.sum(data[final_above_curve_indices, 2])
print('Final total sum:', final_total)
