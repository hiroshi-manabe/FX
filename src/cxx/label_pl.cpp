#include <cstdlib>
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

  if (argc != 3) {
    exit(-1);
  }
  
  int pl_limit;
  int spread_delta;
  stringstream(argv[1]) >> pl_limit;
  stringstream(argv[2]) >> spread_delta;

  string str;
  vector<string> orig_list;
  vector<int> time_list;
  vector<vector<int>> ask_bid_list = {{}, {}};
  vector<int>& ask_list = ask_bid_list[0];
  vector<int>& bid_list = ask_bid_list[1];
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
    int results[2] = { -pl_limit, -pl_limit };

    for (bool is_sell : {false, true}) {
      int index = is_sell ? 1 : 0;
      int profit_sign = is_sell ? -1 : 1;
      int signed_spread_delta = spread_delta * -profit_sign;
      vector<int>& order_list = is_sell ? bid_list : ask_list;
      vector<int>& settle_list = is_sell ? ask_list : bid_list;
      for (size_t j = i; j < orig_list.size(); ++j) {
        int pl = (settle_list[j] + signed_spread_delta - order_list[i]) * profit_sign;
        if (abs(pl) >= pl_limit) {
          results[index] = pl;
          break;
        }
      }
    }
    cout <<  results[0] << ":" << results[1];
    cout << "\n";
  }
}
