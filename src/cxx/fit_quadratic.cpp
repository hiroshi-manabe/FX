// fit_quadratic.cpp  –  Append quadratic-fit coefficients (a,b,c,R²)
// to each row of a weekly tick CSV.
//
// Input  (stdin): CSV rows beginning with
//      0 : time_ms  (milliseconds since week-start)
//      1 : ask_pip  (integer pips, e.g. 142.056 ⇒ 142056)
//      2 : bid_pip  (…)        — remaining fields untouched.
//
// For every <window_ms> supplied on the command line we perform an
// incremental least-squares fit  y = a·x² + b·x + c
// where  x  = (time_ms − cur_time_ms)
//        y  = (ask_pip − cur_ask_pip)        (no 100 000 scaling)
// and append
//     ,<window>:<a>:<b>:<c>:<R2>
// Multiple windows are separated by '/'.
//
// Compile with C++17:
//     g++ -O3 -std=c++17 fit_quadratic.cpp -o fit_quadratic
//--------------------------------------------------------------------
#include <algorithm>
#include <cmath>
#include <iostream>
#include <sstream>
#include <string>
#include <vector>

using std::getline;
using std::size_t;
using std::string;
using std::vector;

struct TickRow {
    long   time_ms;
    long   ask_pip;
    string raw;
};

struct QuadFit { double a{}, b{}, c{}, r2{}; };

// Solve normal equations for quadratic fit
static QuadFit fit_quadratic(const vector<TickRow>& buf)
{
    const size_t n = buf.size();
    if (n < 3) {
        return {};
    }

    const long  cur_t   = buf.back().time_ms;
    const long  cur_pip = buf.back().ask_pip;

    double Sx=0, Sx2=0, Sx3=0, Sx4=0;
    double Sy=0, Sxy=0, Sx2y=0;

    for (const auto& t : buf) {
        double x = static_cast<double>(t.time_ms - cur_t);     // ms offset
        double y = static_cast<double>(t.ask_pip - cur_pip);   // pip delta
        double x2 = x*x;
        Sx   += x;
        Sx2  += x2;
        Sx3  += x2 * x;
        Sx4  += x2 * x2;
        Sy   += y;
        Sxy  += x * y;
        Sx2y += x2 * y;
    }
    const double N = static_cast<double>(n);
    double D =   N*(Sx2*Sx4 - Sx3*Sx3)
               - Sx*(Sx*Sx4 - Sx2*Sx3)
               + Sx2*(Sx*Sx3 - Sx2*Sx2);
    if (std::fabs(D) < 1e-12) return {};

    double Da =   N*(Sx2*Sx2y - Sx3*Sxy)
                - Sx*(Sx*Sx2y - Sx2*Sxy)
                + Sy*(Sx*Sx3 - Sx2*Sx2);
    double Db =   N*(Sxy*Sx4 - Sx3*Sx2y)
                - Sy*(Sx*Sx4 - Sx2*Sx3)
                + Sx2*(Sx*Sx2y - Sx2*Sxy);
    double Dc =   Sy*(Sx2*Sx4 - Sx3*Sx3)
                - Sx*(Sxy*Sx4 - Sx3*Sx2y)
                + Sx2*(Sxy*Sx3 - Sx2*Sx2y);

    QuadFit q;
    q.a = Da / D;
    q.b = Db / D;
    q.c = Dc / D;

    // R²
    double mean = Sy / N;
    double ss_tot = 0.0, ss_res = 0.0;
    for (const auto& t : buf) {
        double x = static_cast<double>(t.time_ms - cur_t);
        double y = static_cast<double>(t.ask_pip - cur_pip);
        double y_pred = q.a*x*x + q.b*x + q.c;
        ss_res += (y - y_pred)*(y - y_pred);
        ss_tot += (y - mean)  * (y - mean);
    }
    q.r2 = (ss_tot < 1e-12) ? 0.0 : 1.0 - ss_res / ss_tot;
    return q;
}
//--------------------------------------------------------------------
int main(int argc, char* argv[])
{
    std::ios::sync_with_stdio(false);

    if (argc < 2) {
        std::cerr << "Usage: fit_quadratic <time_window_ms> ...\n";
        return 1;
    }
    vector<long> windows;
    for (int i = 1; i < argc; ++i) {
        long w = 0; std::stringstream(argv[i]) >> w;
        if (w > 0) {
            windows.push_back(w);
        }
    }
    if (windows.empty()) {
        std::cerr << "No valid windows provided.\n";
        return 1;
    }

    struct WinBuf { long span_ms; vector<TickRow> buf; };
    vector<WinBuf> winbufs;
    for (long w : windows) {
        winbufs.push_back({w, {}});
    }

    string line;
    while (getline(std::cin, line)) {
        if (line.empty()) {
            continue;
        }
        std::stringstream ss(line);
        string field;
        getline(ss, field, ',');
        long t_ms = std::stol(field);
        getline(ss, field, ',');
        long ask_pip = std::stol(field);

        TickRow row{t_ms, ask_pip, line};

        std::ostringstream out;
        out << line;

        for (auto& wb : winbufs) {
            wb.buf.push_back(row);
            while (!wb.buf.empty() &&
                   (t_ms - wb.buf.front().time_ms) > wb.span_ms) {
                wb.buf.erase(wb.buf.begin());
            }

            QuadFit q = { 0 };
            if (t_ms >= wb.span_ms) {
                q = fit_quadratic(wb.buf);
            }
            out << ',' << wb.span_ms << ':' << q.a << ':' << q.b << ':' << q.c << ':' << q.r2;
        }
        std::cout << out.str() << '\n';
    }
    return 0;
}
