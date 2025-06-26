#include <cstdlib>
#include <iostream>
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

/*
 * label_pl.cpp  — determine P/L for a BUY and SELL opened at every tick.
 * A trade closes when either   ±PL_limit   is hit OR when the fixed
 * decision-horizon (ms) elapses.  Entry prices are *spread-adjusted* to
 * reflect a real broker spread: we treat the BUY entry as ask0+spread_delta
 * and the SELL entry as bid0-spread_delta.
 *
 * Output row:  original baseline columns +
 *              buyPL:buyExitTs:sellPL:sellExitTs  (col 5)
 *
 * CLI: label_pl <pl_limit> <spread_delta> <decision_horizon_ms>
 */

int main(int argc, char *argv[]) {
    std::ios::sync_with_stdio(false);
    if (argc != 4) {
        std::cerr << "Usage: label_pl <pl_limit> <spread_delta> <decision_horizon_ms>" << std::endl;
        return -1;
    }
    int pl_limit, spread_delta, horizon_ms;
    stringstream(argv[1]) >> pl_limit;
    stringstream(argv[2]) >> spread_delta;
    stringstream(argv[3]) >> horizon_ms;

    // Load entire tick list
    vector<string> raw_rows;
    vector<int> time_list, ask_list, bid_list;
    string line;
    while (cin >> line) {
        raw_rows.push_back(line);
        string tok; int v;
        stringstream ss(line);
        // time
        getline(ss, tok, ','); stringstream(tok) >> v; time_list.push_back(v);
        // ask
        getline(ss, tok, ','); stringstream(tok) >> v; ask_list.push_back(v);
        // bid
        getline(ss, tok, ','); stringstream(tok) >> v; bid_list.push_back(v);
    }
    const size_t N = raw_rows.size();

    for (size_t i = 0; i < N; ++i) {
        int ask0 = ask_list[i];
        int bid0 = bid_list[i];
        int t0   = time_list[i];

        // **** spread-adjusted entry prices ****
        double ask_entry = ask0 + spread_delta; // BUY entry price
        double bid_entry = bid0 - spread_delta; // SELL entry price

        int buy_pl  = 0,  sell_pl  = 0;
        int buy_ts  = -1, sell_ts  = -1;

        for (size_t k = i; k < N; ++k) {
            int tk   = time_list[k];
            int askk = ask_list[k];
            int bidk = bid_list[k];
            int dt   = tk - t0;

            // BUY position
            if (buy_ts == -1) {
                if (askk - ask_entry >= pl_limit) {
                    buy_pl =  pl_limit; buy_ts = tk;
                } else if (bidk - ask_entry <= -pl_limit) {
                    buy_pl = -pl_limit; buy_ts = tk;
                } else if (horizon_ms != 0 && dt >= horizon_ms) {
                    buy_pl = askk - ask_entry; buy_ts = tk;
                }
            }
            // SELL position
            if (sell_ts == -1) {
                if (bid_entry - bidk >= pl_limit) {
                    sell_pl =  pl_limit; sell_ts = tk;
                } else if (askk - bid_entry >= pl_limit) {
                    sell_pl = -pl_limit; sell_ts = tk;
                } else if (horizon_ms != 0 && dt >= horizon_ms) {
                    sell_pl = bid_entry - bidk; sell_ts = tk;
                }
            }
            if (buy_ts != -1 && sell_ts != -1) break;
        }

        // fallback close at last tick if never triggered
        if (buy_ts == -1) {
            buy_pl = ask_list.back() - ask_entry; buy_ts = time_list.back();
        }
        if (sell_ts == -1) {
            sell_pl = bid_entry - bid_list.back(); sell_ts = time_list.back();
        }

        // emit row + result block
        bool buy_nohit  = std::abs(buy_pl)  < pl_limit;
        bool sell_nohit = std::abs(sell_pl) < pl_limit;

        cout << raw_rows[i] << ','
             << buy_pl  << ':' << buy_ts  << ':'
             << sell_pl << ':' << sell_ts << ':'
             << buy_nohit  << ':' << sell_nohit << '\n';    }
    return 0;
}
