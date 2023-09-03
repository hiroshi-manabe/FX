#!/usr/bin/env perl
use strict;
use warnings;

use Config::Simple;

my $cfg = new Config::Simple('config.ini');
my $currency = $cfg->param('settings.currency_pair');
my @window_times = @{$cfg->param('settings.window_times')};
my @window_times_quarter = map { int($_ / 4) } @window_times;
my @r_squared_values = qw(0.9400 0.9425 0.9450 0.9475 0.9500 0.9525 0.9550 0.9575 0.9600 0.9625 0.9650 0.9675 0.9700 0.9725 0.9750 0.9775 0.9800 0.9825 0.9850 0.9875 0.9900);
$cfg->param("settings.r_squared_values", \@r_squared_values);
$cfg->save();

system("php download.php");
system("./update.pl");
system("./make_week_data.pl 60");
system("./add_data.pl 50");
system("./add_past_data.pl");
system("./make_past_data.pl");
system("./parameter_search.pl 0 59 20");
system("./test_runner.pl");

#./parameter_search.pl 50 20 20
#./test.py --stdin --num_processes 8 < commands.txt
#./generate_csv.pl 39
#./find_optimal.py 39 | ./report_to_params.pl > USDJPY/results_39/params.csv 
# cat USDJPY/results_39/params.csv | perl -F/,/ -nale '$cmd = qq{./test.py 20 39 40 40 --k_value $F[2] --threshold $F[3] --window_time $F[0] --r_squared_value $F[1]}; print $cmd; system $cmd;' 
#./generate_csv.pl 40
#./find_optimal.py 40 | ./report_to_params.pl > USDJPY/results_40/params.csv
# cat USDJPY/results_40/params.csv | perl -F/,/ -nale '$cmd = qq{./test.py 21 40 41 41 --k_value $F[2] --threshold $F[3] --window_time $F[0] --r_squared_value $F[1]}; print $cmd; system $cmd;' 
