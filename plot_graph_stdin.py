#!/usr/bin/env python3
import sys
import argparse
import matplotlib.pyplot as plt

def main(output_file):
    data = sys.stdin.readlines()
    x, y = [], []

    for line in data:
        x_value, y_value = line.strip().split(",")
        x.append(float(x_value))
        y.append(float(y_value))

    plt.plot(x, y)
    plt.savefig(output_file)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Plot graph and save as PNG file.')
    parser.add_argument('output_file', type=str, help='The output PNG file name.')

    args = parser.parse_args()

    main(args.output_file)
