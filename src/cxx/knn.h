#pragma once
#include <vector>
#include <string>

extern "C" {
  void k_nearest_neighbors(double first_coef, double second_coef,
                           const double *flattened_data, int num_data_points,
                           int k, int *output_array);
}
