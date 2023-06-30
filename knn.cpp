#include "knn.h"
#include <algorithm>
#include <cmath>
#include <limits>

struct Neighbor {
  double distance;
  int index;

  bool operator<(const Neighbor &other) const {
    return distance < other.distance;
  }
};

extern "C" {
  void k_nearest_neighbors(double first_coef, double second_coef,
                          const double *flattened_data, int num_data_points,
                          int k, int *output_array) {
    // Reconstruct train_data from the flattened_data
    std::vector<std::vector<double>> train_data;
    for (int i = 0; i < num_data_points; ++i) {
      std::vector<double> row(flattened_data + i * 2, flattened_data + i * 2 + 2);
      train_data.push_back(row);
    }

    // Calculate the distances between the given data point and all past data points
    std::vector<Neighbor> distances(train_data.size());
    for (size_t i = 0; i < train_data.size(); i++) {
      const auto &past_point = train_data[i];
      double distance = std::pow(past_point[0] - first_coef, 2) + std::pow(past_point[1] - second_coef, 2);
      distances[i] = {distance, static_cast<int>(i)};
    }

    // Find the k nearest neighbors
    std::partial_sort(distances.begin(), distances.begin() + k, distances.end());
    std::vector<Neighbor> nearest_neighbors(distances.begin(), distances.begin() + k);

    for (int i = 0; i < k; ++i) {
      output_array[i] = nearest_neighbors[i].index;
    }
    return;
  }
}
