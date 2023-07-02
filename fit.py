#/usr/bin/python3
import time
import numpy as np
import matplotlib.pyplot as plt
import re
import subprocess

def quadratic(x, a, b, c):
    return a * x**2 + b * x + c

in_filename = "temp3.csv"
out_filename = re.sub(r"\.csv$", ".png", in_filename)
data = np.loadtxt(in_filename, delimiter=",", unpack=True)
fig = plt.figure()
plt.plot(data[0], data[1], color="red")

with open(in_filename, 'r') as f_in:
    input_data = f_in.read()

result = subprocess.run(['./fit'], capture_output=True, text=True, input=input_data)
output_lines = result.stdout.strip().split('\n')
c = [float(x) for x in output_lines]
print(c)

# データの準備
x = data[0]
y = data[1]

# 予測値の計算
y_pred = quadratic(x, c[2], c[1], c[0])

# 残差の二乗和と全変動の二乗和の計算
ss_res = np.sum((y - y_pred)**2)
ss_tot = np.sum((y - np.mean(y))**2)

# 決定係数の計算
r_squared = 1 - (ss_res / ss_tot)
print(r_squared)

data2 = [[], []]
for i in range(int(data[0][0]), 99, 100):
    if i > 0:
        i = 0
    data2[0].append(i)
    data2[1].append(c[0] + c[1] * i + c[2] * i * i)

plt.plot(data2[0], data2[1], color="blue")
plt.savefig(out_filename, dpi=fig.dpi)
plt.clf()
plt.close()
