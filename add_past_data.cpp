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

  if (argc < 2) {
    cerr << "Usage: add_past_data <time_width> ...\n";
    exit(-1);
  }

  int time_widths[100] = {0};
  int n = argc - 1;
  for (int i = 0; i < n; ++i) {
    stringstream(argv[1 + i]) >> time_widths[i];
  }
  
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

  int price_to_normalize = 100000;
  
  for (int i = 0; i < orig_list.size(); ++i) {
    int cur_time = time_list[i];
    int cur_price = price_list[i];
    double rate = (double)cur_price / price_to_normalize;

    cout << orig_list[i] << ",";
    stringstream ss_coeff;
    for (int j = 0; j < n; ++j) {
      ss_coeff << time_widths[j] << ":";
      if (cur_time >= time_widths[j] - 1) {
        int start_time = cur_time - time_widths[j] + 1;

        double X[5] = {0};
        double Y[3] = {0};
        for (int k = i; time_list[k] >= start_time && k >= 0; --k) {
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
        double ss_res = 0.0;
        double ss_tot = 0.0;
        
        for (int k = i; time_list[k] >= start_time && k >= 0; --k) {
          int time = time_list[k];
          double price = (double)price_list[k] / rate;
          double x = (double)time - cur_time;
          double y = (double)price - price_to_normalize;
          double y_pred = quadratic(x, coeffs[2], coeffs[1], coeffs[0]);
          double t = y - y_pred;
          ss_res += t * t;
          t = y - y_mean;
          ss_tot += t * t;
        }
        double r_squared = 1 - (ss_res / ss_tot);
        ss_coeff.precision(17);
        for (const auto &t : coeffs) {
          ss_coeff << t;
          ss_coeff << ":";
        }
        ss_coeff << r_squared;
      }
      else {
        ss_coeff << "0.0:0.0:0.0:0.0";
      }
      if (j < n - 1) {
        ss_coeff << "/";
      }
    }
    cout << ss_coeff.str() << "\n";
  }
}
