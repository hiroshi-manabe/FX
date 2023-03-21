#include <cmath>
#include <cstdio>
#include <iostream>
#include <istream>
#include <sstream>
#include <string>
#include <vector>

using std::abs;
using std::cerr;
using std::cin;
using std::cout;
using std::dec;
using std::getline;
using std::hex;
using std::size_t;
using std::string;
using std::stringstream;
using std::vector;

bool fitIt( 
  const double* X,
  const double* Y,
  const int &order,
  vector<double> &coeffs)
{
  int n = order;
  int np1 = n + 1;
  int np2 = n + 2;
  int tnp1 = 2 * n + 1;
  double tmp;

  // a = vector to store final coefficients.
  vector<double> a(np1);

  // B = normal augmented matrix that stores the equations.
  vector<vector<double> > B(np1, vector<double> (np2, 0));

  for (int i = 0; i <= n; ++i) {
    for (int j = 0; j <= n; ++j) {
      B[i][j] = X[i + j];
    }
  }

  // Load values of Y as last column of B
  for (int i = 0; i <= n; ++i) {
    B[i][np1] = Y[i];
  }

  n += 1;
  int nm1 = n-1;

  // Pivotisation of the B matrix.
  for (int i = 0; i < n; ++i) {
    for (int k = i+1; k < n; ++k) {
      if (B[i][i] < B[k][i]) {
        for (int j = 0; j <= n; ++j) {
          tmp = B[i][j];
          B[i][j] = B[k][j];
          B[k][j] = tmp;
        }
      }
    }
  }

  // Performs the Gaussian elimination.
  // (1) Make all elements below the pivot equals to zero
  //     or eliminate the variable.
  for (int i=0; i<nm1; ++i) {
    for (int k =i+1; k<n; ++k) {
      double t = B[k][i] / B[i][i];
      for (int j=0; j<=n; ++j) {
        B[k][j] -= t*B[i][j];         // (1)
      }
    }
  }

  // Back substitution.
  // (1) Set the variable as the rhs of last equation
  // (2) Subtract all lhs values except the target coefficient.
  // (3) Divide rhs by coefficient of variable being calculated.
  for (int i=nm1; i >= 0; --i) {
    a[i] = B[i][n];                   // (1)
    for (int j = 0; j<n; ++j) {
      if (j != i) {
        a[i] -= B[i][j] * a[j];       // (2)
      }
    }
    a[i] /= B[i][i];                  // (3)
  }

  coeffs.resize(a.size());
  for (size_t i = 0; i < a.size(); ++i) {
    coeffs[i] = a[i];
  }

  return true;
}

double quadratic(double x, double a, double b, double c) {
  return a * x * x + b * x + c;
}

int main(int argc, char *argv[]) {
  std::ios::sync_with_stdio(false);

  if (argc < 4) {
    cerr << "Usage: add_past_data <bit_width> <bit_height> <time_width> ...\n";
    exit(-1);
  }

  int max_speed;
  int bit_width;
  int time_widths[100] = {0};
  int time_factors[100] = {0};
  int n = argc - 3;
  int bit_height;
  stringstream(argv[1]) >> bit_width;
  stringstream(argv[2]) >> bit_height;
  for (int i = 0; i < n; ++i) {
    stringstream(argv[3 + i]) >> time_widths[i];
    time_factors[i] = time_widths[i] / bit_width;
  }
  int byte_count = (bit_width * bit_height - 1) / 8 + 1;
  
  string str;
  vector<string> orig_list;
  vector<int> time_list;
  vector<int> price_list;
  while (cin >> str) {
    orig_list.push_back(str);
    stringstream sstr(str);
    string t;
    int i;
    getline(sstr, t, ',');
    stringstream(t) >> i;
    time_list.push_back(i);
    getline(sstr, t, ',');
    stringstream(t) >> i;
    price_list.push_back(i);
  }
  int movement_width = 300000;
  int movement = 0;
  int movement_start_index = 0;

  int price_to_normalize = 100000;
  
  for (int i = 0; i < orig_list.size(); ++i) {
    int cur_time = time_list[i];
    int cur_price = price_list[i];
    double rate = (double)cur_price / price_to_normalize;
    if (i > 0) {
      movement += abs(cur_price - price_list[i-1]);
    }
    while (cur_time - movement_width > time_list[movement_start_index]) {
      movement_start_index++;
      movement -= abs(price_list[movement_start_index] - price_list[movement_start_index-1]);
    }

    int movement_normalized = (int)((double)movement / rate);
    cout << orig_list[i] << "," << movement_normalized << ",";
    stringstream ss_bit;
    stringstream ss_coeff;
    for (int j = 0; j < n; ++j) {
      ss_bit << time_widths[j] << ":";
      ss_coeff << time_widths[j] << ":";
      if (cur_time >= time_widths[j] - 1) {
        int start_time = cur_time - time_widths[j] + 1;
        int min_rel_price = 0;
        int max_rel_price = 0;
        unsigned char bits[1024] = { 0 }; // some big number

        double X[5] = {0};
        double Y[3] = {0};
        for (int k = i; time_list[k] >= start_time && k >= 0; --k) {
          int rel_price = int((double)price_list[k] / rate) - price_to_normalize;
          if (rel_price < min_rel_price) {
            min_rel_price = rel_price;
          }
          else if (rel_price > max_rel_price) {
            max_rel_price = rel_price;
          }
          
          double x = (double)time_list[k] - cur_time;
          double y = (double)price_list[k] / rate - price_to_normalize;
          X[0] += 1;
          X[1] += x;
          double t = x * x;
          X[2] += t;
          t *= x;
          X[3] += t;
          t *= x;
          X[4] += t;
          t = y;
          Y[0] += t;
          t *= x;
          Y[1] += t;
          t *= x;
          Y[2] += t;
        }
        vector<double> coeffs;
        fitIt(X, Y, 2, coeffs);
        double y_mean = Y[0] / X[0];
        
        int max_rel_price_bits = bit_height / 2 - 1;
        int min_rel_price_bits = -(bit_height / 2);
        int price_factor_min = (-min_rel_price + -min_rel_price_bits - 1) / -min_rel_price_bits;
        int price_factor_max = (max_rel_price + max_rel_price_bits - 1) / max_rel_price_bits;
        int price_factor = 1;
        if (price_factor_min > price_factor) {
          price_factor = price_factor_min;
        }
        if (price_factor_max > price_factor) {
          price_factor = price_factor_max;
        }
        int min_price = price_to_normalize + (min_rel_price_bits * price_factor);
        double ss_res = 0.0;
        double ss_tot = 0.0;
        
        for (int k = i; time_list[k] >= start_time && k >= 0; --k) {
          int time = time_list[k];
          int price = int((double)price_list[k] / rate);
          int time_diff = time - start_time;
          int price_diff = price - min_price;
          int time_index = time_diff / time_factors[j];
          int price_index = price_diff / price_factor;
          int bit_pos = price_index + time_index * bit_height;
          int byte_index = bit_pos >> 3;
          int bit_data = 1 << (bit_pos % 8);
          if (price_diff >= 0 && price_index < bit_height) {
            bits[byte_index] |= bit_data;
          }
          
          double x = (double)time_list[k] - cur_time;
          double y = (double)price_list[k] / rate - price_to_normalize;
          double y_pred = quadratic(x, coeffs[2], coeffs[1], coeffs[0]);
          double t = y - y_pred;
          ss_res += t * t;
          t = y - y_mean;
          ss_tot += t * t;
          //          if (i % 10000 == 0) {
          //            cerr << "x " << x << " y " << y << " y_pred " << y_pred << " y_mean " << y_mean << " ss_res " << ss_res << " ss_tot " << ss_tot << "\n";
          //          }
        }
        double r_squared = 1 - (ss_res / ss_tot);
        ss_bit << price_factor << ":";
        for (int k = 0; k < byte_count; ++k) {
          char buf[3];
          snprintf(buf, 3, "%02x", bits[k]);
          ss_bit << buf;
        }
        ss_coeff.precision(17);
        for (const auto &t : coeffs) {
          ss_coeff << t;
          ss_coeff << ":";
        }
        ss_coeff << r_squared;
      }
      else {
        ss_bit << 0 << ":";
        const char buf[3] = "ff";
        for (int k = 0; k < byte_count; ++k) {
          ss_bit << buf;
        }
        ss_coeff << "0.0:0.0:0.0:0.0";
      }
      if (j < n - 1) {
        ss_bit << "/";
        ss_coeff << "/";
      }
    }
    cout << ss_bit.str() << ",";
    cout << ss_coeff.str() << "\n";
  }
}
