import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

# Load the data from the file
data = pd.read_csv('data.txt', delimiter='\t', header=None).values

# Cap and floor the third column values at -50 and 50
data[:, 6] = np.clip(data[:, 6], -50, 50)

# Generate colors
colors = plt.cm.coolwarm((data[:, 6] + 50) / 100) # as coolwarm maps between 0 and 1, we adjust our data accordingly

plt.scatter(data[:, 4], data[:, 5], color=colors, s=5)

# Define the quadratic function
def quad_func(params, x):
    a, b, c = params
    return a*x**2 + b*x + c

# Generate x values
x_values = np.linspace(np.min(data[:,0]), np.max(data[:,0]), 400)

# Compute y values
y_values = quad_func([0.26255675, 0.02321278, 0.14728814], x_values)

# Plot quadratic curve
#plt.plot(x_values, y_values, 'k--')

# Show plot
plt.show()

