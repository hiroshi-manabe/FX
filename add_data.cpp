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

  if (argc != 3) {
    exit(-1);
  }

  int width;
  int time;
  
  stringstream(argv[1]) >> width;
  stringstream(argv[2]) >> time;
  
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
    int result = 0;
    int result_time = -1;
    for (size_t j = i; j < orig_list.size(); ++j) {
      if (ask_list[j] >= ask + width) {
        result = width;
        result_time = time_list[j];
        break;
      }
      else if (ask_list[j] <= ask - width) {
        result = -width;
        result_time = time_list[j];
        break;
      }
      else if (time && (time_list[j] >= start_time + time)) {
        result = ask_list[j] - ask;
        result_time = time_list[j];
        break;
      }
    }
    cout << result << ":" << result_time;
    cout << "\n";
  }
}
