#include <iostream>
#include <istream>
#include <sstream>
#include <string>
#include <vector>

using std::cin;
using std::cout;
using std::fill_n;
using std::getline;
using std::size_t;
using std::string;
using std::stringstream;
using std::vector;

int main(int argc, char *argv[]) {
  std::ios::sync_with_stdio(false);

  if (argc < 3 || argc > 102) {
    exit(-1);
  }
  
  int n = argc - 2;
  int width = 0;
  int window_times[100] = {0};
  int losscut;
  stringstream(argv[1]) >> losscut;

  for (int i = 0; i < n; ++i) {
    stringstream(argv[i + 2]) >> window_times[i];
  }
  
  string str;
  vector<string> orig_list;
  vector<int> time_list;
  vector<int> ask_list;
  vector<int> bid_list;
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
    ask_list.push_back(i);
    getline(sstr, t, ',');
    stringstream(t) >> i;
    bid_list.push_back(i);
  }
  for (size_t i = 0; i < orig_list.size(); ++i) {
    cout << orig_list[i] << ",";
    int ask = ask_list[i];
    int start_time = time_list[i];
    int results[2][100] = {{0}, {0}};
    int result_times[2][100];
    fill_n(&result_times[0][0], 2 * 100, -1);

    for (int buy_or_sell = 0; buy_or_sell < 2; ++buy_or_sell) {
      for (size_t j = 0; j < n; ++j) {
        for (size_t k = i; k < orig_list.size(); ++k) {
          bool should_exit_trade = false;
          int window_time = window_times[j];
          int desired_diff = (buy_or_sell == 0) ? 1 : -1;
          
          if ((ask_list[k] - ask_list[i]) * desired_diff <= -losscut) {
            should_exit_trade = true;
          }
          else if (time_list[k] > start_time + window_time) {
            int index_before_window = k;

            while (time_list[index_before_window] > time_list[k] - window_time) {
              --index_before_window;
            }

            if ((ask_list[k] - ask_list[index_before_window]) * desired_diff < 0) {
              should_exit_trade = true;
            }
          }

          if (should_exit_trade) {
            results[buy_or_sell][j] = (buy_or_sell == 0 ? 1 : -1) * (ask_list[k] - ask);
            result_times[buy_or_sell][j] = time_list[k];
            break;
          }
        }
      }
    }
    for (size_t j = 0; j < n; ++j) {
      cout << window_times[j] << ":" << results[0][j] << ":" << result_times[0][j] << ":" << results[1][j] << ":" << result_times[1][j];
      if (j < n - 1) {
        cout << "/";
      }
    }
    cout << "\n";
  }
}
