#!/usr/bin/env perl
use strict;
use warnings;

system("php download.php");
system("./update.pl");
system("./make_week_data.pl 45");
system("./label_pl.pl");
system("./fit_quadratic.pl");
system("./filter_digest.pl");
system("./parameter_search.pl 0 44 15");
system("./generate_csv.pl 44 15");
system("./extract_matching.pl 44 15 > result_all.txt");

#./parameter_search.pl 50 20 20
#./test.py --stdin --num_processes 8 < commands.txt
#./generate_csv.pl 50 20
#./find_optimal.py 39 | ./report_to_params.pl > USDJPY/results_39/params.csv 
# cat USDJPY/results_39/params.csv | perl -F/,/ -nale '$cmd = qq{./test.py 20 39 40 40 --k_value $F[2] --threshold $F[3] --window_time $F[0] --r_squared_value $F[1]}; print $cmd; system $cmd;' 
#./generate_csv.pl 40
#./find_optimal.py 40 | ./report_to_params.pl > USDJPY/results_40/params.csv
# cat USDJPY/results_40/params.csv | perl -F/,/ -nale '$cmd = qq{./test.py 21 40 41 41 --k_value $F[2] --threshold $F[3] --window_time $F[0] --r_squared_value $F[1]}; print $cmd; system $cmd;' 
