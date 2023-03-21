#!/usr/bin/env python3
import sys
import matplotlib.pyplot as plt

def main():
    data = sys.stdin.readlines()
    x, y = [], []

    for line in data:
        x_value, y_value = line.strip().split(",")
        x.append(float(x_value))
        y.append(float(y_value))

    plt.plot(x, y)
    plt.show()

if __name__ == "__main__":
    main()
