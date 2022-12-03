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

  if (argc < 4) {
    cerr << "Usage: add_past_data <bit_width> <bit_height> <time_width> ...\n";
    exit(-1);
  }

  int bit_width;
  int time_widths[10] = {0};
  int time_factors[10] = {0};
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
  for (int i = 0; i < orig_list.size(); ++i) {
    cout << orig_list[i] << ",";
    for (int j = 0; j < n; ++j) {
      cout << time_widths[j] << ":";
      int cur_time = time_list[i];
      if (cur_time >= time_widths[j] - 1) {
        int start_time = cur_time - time_widths[j] + 1;
        int cur_price = price_list[i];
        int min_rel_price = 0;
        int max_rel_price = 0;
        unsigned char bits[1024] = { 0 }; // some big number
        for (int k = i; time_list[k] >= start_time && k >= 0; --k) {
          int rel_price = price_list[k] - cur_price;
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
        for (int k = i; time_list[k] >= start_time && k >= 0; --k) {
          int time = time_list[k];
          int price = price_list[k];
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
        }
        cout << price_factor << ":";
        for (int k = 0; k < byte_count; ++k) {
          char buf[3];
          snprintf(buf, 3, "%02x", bits[k]);
          cout << buf;
        }
      }
      else {
        cout << 0 << ":";
        const char buf[3] = "ff";
        for (int k = 0; k < byte_count; ++k) {
          cout << buf;
        }
      }
      if (j < n - 1) {
        cout << "/";
      }
    }
    cout << "\n";
  }
}
