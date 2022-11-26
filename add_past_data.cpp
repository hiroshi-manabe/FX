#include <cstdio>
#include <iostream>
#include <istream>
#include <sstream>
#include <string>
#include <vector>

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

int main(int argc, char *argv[]) {
  std::ios::sync_with_stdio(false);

  if (argc != 4) {
    cerr << "Usage: add_past_data <bit_width> <time_width> <bit_height>\n";
    exit(-1);
  }

  int bit_width;
  int time_width;
  int bit_height;
  stringstream(argv[1]) >> bit_width;
  stringstream(argv[2]) >> time_width;
  stringstream(argv[3]) >> bit_height;

  int byte_count = (bit_width * bit_height - 1) / 8 + 1;
  int time_factor = time_width / bit_width;
  
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
  for (int i = 0; i < orig_list.size(); ++i) {
    cout << orig_list[i] << ",";
    int cur_time = time_list[i];
    if (cur_time >= time_width - 1) {
      int start_time = cur_time - time_width + 1;
      int cur_price = price_list[i];
      int min_rel_price = 0;
      int max_rel_price = 0;
      unsigned char bits[1024] = { 0 }; // some big number
      for (int j = i; time_list[j] >= start_time && j >= 0; --j) {
        int rel_price = price_list[j] - cur_price;
        if (rel_price < min_rel_price) {
          min_rel_price = rel_price;
        }
        else if (rel_price > max_rel_price) {
          max_rel_price = rel_price;
        }
      }
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
      int min_price = cur_price + (min_rel_price_bits * price_factor);
      for (int j = i; time_list[j] >= start_time && j >= 0; --j) {
        int time = time_list[j];
        int price = price_list[j];
        int time_diff = time - start_time;
        int price_diff = price - min_price;
        int time_index = time_diff / time_factor;
        int price_index = price_diff / price_factor;
        int bit_pos = price_index + time_index * bit_height;
        int byte_index = bit_pos >> 3;
        int bit_data = 1 << (bit_pos % 8);
        if (price_diff >= 0 && price_index < bit_height) {
          bits[byte_index] |= bit_data;
        }
      }
      cout << price_factor << ":";
      for (int j = 0; j < byte_count; ++j) {
        char buf[3];
        snprintf(buf, 3, "%02x", bits[j]);
        cout << buf;
      }
    }
    cout << "\n";
  }
}
