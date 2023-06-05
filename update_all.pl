#!/usr/bin/env perl
use strict;
use warnings;

use Config::Simple;

my $cfg = new Config::Simple('config.ini');
my $currency = $cfg->param('settings.currency_pair');
my @window_times = @{$cfg->param('settings.window_times')};
my @window_times_quarter = map { int($_ / 4) } @window_times;
my @r_squared_values = @{$cfg->param('settings.r_squared_values')};

#system("php download.php");
#system("./update.pl");
#system("./make_week_data.pl 52");
#system("./add_data.pl 50 ".join(" ", @window_times_quarter));
#system("./add_past_data.pl ".join(" ", @window_times));
system("./make_past_data.pl");
#system("./parameter_search_runner.pl");
#system("./test_all.pl");
#./parameter_search.pl 50 20 20
#./test.py --stdin --num_processes 8 < commands.txt
#./generate_csv.pl 39
#./find_optimal.py 39 | ./report_to_params.pl > USDJPY/results_39/params.csv 
# cat USDJPY/results_39/params.csv | perl -F/,/ -nale '$cmd = qq{./test.py 20 39 40 40 --k_value $F[2] --threshold $F[3] --window_time $F[0] --r_squared_value $F[1]}; print $cmd; system $cmd;' 
#./generate_csv.pl 40
#./find_optimal.py 40 | ./report_to_params.pl > USDJPY/results_40/params.csv
# cat USDJPY/results_40/params.csv | perl -F/,/ -nale '$cmd = qq{./test.py 21 40 41 41 --k_value $F[2] --threshold $F[3] --window_time $F[0] --r_squared_value $F[1]}; print $cmd; system $cmd;' 
