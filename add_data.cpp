#include <iostream>
#include <istream>
#include <sstream>
#include <string>
#include <vector>

using std::cin;
using std::cout;
using std::getline;
using std::size_t;
using std::string;
using std::stringstream;
using std::vector;

int main(int argc, char *argv[]) {
  std::ios::sync_with_stdio(false);

  if (argc < 3 || argc > 21 || argc % 2 == 0) {
    exit(-1);
  }
  
  int n = (argc - 1) / 2;
  int widths[10] = {0};
  int times[10] = {0};

  for (int i = 0; i < n; ++i) {
    stringstream(argv[i * 2 + 1]) >> widths[i];
    stringstream(argv[i * 2 + 2]) >> times[i];
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
    int results[10] = {0};
    int result_times[10] = {-1,-1,-1,-1,-1,-1,-1,-1,-1,-1};
    for (size_t j = 0; j < n; ++j) {
      for (size_t k = i; k < orig_list.size(); ++k) {
        if (ask_list[k] >= ask + widths[j]) {
          results[j] = widths[j];
          result_times[j] = time_list[k];
          break;
        }
        else if (ask_list[k] <= ask - widths[j]) {
          results[j] = -widths[j];
          result_times[j] = time_list[k];
          break;
        }
        else if (times[j] && (time_list[k] >= start_time + times[j])) {
          results[j] = ask_list[k] - ask;
          result_times[j] = time_list[k];
          break;
        }
      }
    }
    for (size_t i = 0; i < n; ++i) {
      cout << times[i] << ":" << results[i] << ":" << result_times[i];
      if (i < n - 1) {
        cout << "/";
      }
    }
    cout << "\n";
  }
}
