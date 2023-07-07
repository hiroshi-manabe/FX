#include <iostream>
#include <iomanip>
#include <sstream>
#include <vector>
#include <string>
#include <unordered_map>
#include <algorithm>

using std::cin;
using std::cout;
using std::getline;
using std::setprecision;
using std::stod;
using std::stoi;
using std::string;
using std::stringstream;
using std::unordered_map;
using std::vector;

int main(int argc, char *argv[]) {
  std::ios::sync_with_stdio(false);

  if (argc < 2 || argc > 101) {
    exit(-1);
  }
  string r_squared_value_strs[100];

  int n = argc - 1;
  for (int i = 0; i < n; ++i) {
    stringstream(argv[i + 1]) >> r_squared_value_strs[i];
  }

  vector<vector<string>> data;
  vector<int> time_data;
  unordered_map<int, unordered_map<string, int>> prev_time_dict;

  string line;
  int i = 0;
  while (cin >> line) {
    vector<string> temp;
    stringstream ss(line);
    string val;
    while (getline(ss, val, ',')) {
      temp.push_back(val);
    }
    i = time_data.size();
    time_data.push_back(stoi(temp[0]));

    string token;
    
    vector<string> future_data;
    stringstream ss_future(temp[5]);
    while (getline(ss_future, token, '/')) {
      future_data.push_back(token);
    }

    vector<string> coeffs_data;
    stringstream ss_coeffs(temp[6]);
    while (getline(ss_coeffs, token, '/')) {
      coeffs_data.push_back(token);
    }

    for (int l = 0; l < future_data.size(); l++) {
      vector<string> record;
      stringstream ss_record(future_data[l]);
      while (getline(ss_record, token, ':')) {
        record.push_back(token);
      }
      vector<string> coeffs_record;
      stringstream ss_coeffs_record(coeffs_data[l]);
      while (getline(ss_coeffs_record, token, ':')) {
        coeffs_record.push_back(token);
      }
      int future_width = stoi(record[0]);
      int buy_profit = stoi(record[1]);
      int end_time_buy = stoi(record[2]);
      int sell_profit = stoi(record[3]);
      int end_time_sell = stoi(record[4]);

      int past_width = stoi(coeffs_record[0]);
      
      double coeffs[3] = { stod(coeffs_record[1]), stod(coeffs_record[2]), stod(coeffs_record[3]) };
      double fit = stod(coeffs_record[4]);

      bool density_checked = false;
      bool density_ok = false;
      for (int m = 0; m < n; ++m) {
        string r_squared_value_str = r_squared_value_strs[m];
        double r_squared_value = stod(r_squared_value_str);
        if (abs(coeffs[0]) < 3 && fit > r_squared_value && time_data[i] > prev_time_dict[past_width][r_squared_value_str] + past_width + future_width) {
          if (!density_checked) {
            density_checked = true;
            int j = i;
            while (time_data[j] > time_data[i] - past_width && j > 0) {
              --j;
            }
            ++j;

            if (i == j || (double)past_width / (i - j) > 250) {
              density_ok = false;
              continue;
            }
            else {
              density_ok = true;
            }
          }
          else {
            if (!density_ok) {
              continue;
            }
          }
          cout << temp[0] << "," << past_width << "," << setprecision(8) << r_squared_value_str << "," << setprecision(16) << coeffs[1] << "," << coeffs[2] << "," << buy_profit << "," << sell_profit << "\n";
          prev_time_dict[past_width][r_squared_value_str] = time_data[i];
        }
      }
    }
  }
  return 0;
}
