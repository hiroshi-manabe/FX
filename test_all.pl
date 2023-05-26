#!/usr/bin/env perl
use strict;
use utf8;
use open IO => ':utf8', ':std';

use Config::Simple;

my $cfg = new Config::Simple('config.ini');
my $currency = $cfg->param('settings.currency_pair');

sub printex {
    my $cmd = shift;
    print "$cmd\n";
    system $cmd;
}

my $cmd;

open OUT, ">", "commands.txt";
for my $i(40..51) {
    my $j = $i - 1;
    $cmd = qq{./generate_csv.pl $j};
    print OUT "$cmd\n";
    $cmd = qq{./generate_summary_tables.pl $j};
    print OUT "$cmd\n";
}
$cmd = qq{parallel -j 8 :::: commands.txt};
printex($cmd);
close OUT;

open OUT, ">", "commands.txt";
for my $i(40..51) {
    my $j = $i - 1;
    my $k = $i - 20;
    my $params_path = qq{$currency/results_$j/params.csv};
    $cmd = qq{./find_optimal.py $j | ./report_to_params.pl > $params_path};
    printex($cmd);
    open IN, "<", $params_path or die "$params_path $!";
    while (<IN>) {
        chomp;
        my ($window_time, $r_squared_value, $k_value, $threshold_value, $bet) = split/,/;
        my $output_file = qq{$currency/results_$j/${window_time}_result.txt};
        $cmd = qq{./test.py $k $j $i $i --min_k_value 5 --max_k_value 10 --window_time $window_time --r_squared_value $r_squared_value | ./filter_result.pl $k_value $threshold_value > $output_file};
        print OUT "$cmd\n";
    }
}
$cmd = qq{parallel -j 8 :::: commands.txt};
printex($cmd);
