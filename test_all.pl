#!/usr/bin/env perl
use strict;
use utf8;
use open IO => ':utf8', ':std';

use Config::Simple;

my $cfg = new Config::Simple('config.ini');
my $currency = $cfg->param('settings.currency_pair');

my $last_week = $ARGV[0] // 59;      # Default value is 59 if not provided
my $test_week_num = $ARGV[1] // 20;  # Default value is 20 if not provided
my $test_begin_week = $last_week - $test_week_num;


sub printex {
    my $cmd = shift;
    print STDERR "$cmd\n";
    system $cmd;
}

my $cmd;

open OUT, ">", "commands.txt";
for my $i($test_begin_week..$last_week) {
    $cmd = qq{./generate_csv.pl $i};
    print OUT "$cmd\n";
}
$cmd = qq{parallel -j 8 :::: commands.txt};
printex($cmd);
close OUT;

for my $i($test_begin_week..$last_week) {
    my $k = $i - 20;
    my $params_path = qq{$currency/results_$i/params.csv};
    $cmd = qq{./find_optimal.py $i > $params_path};
    printex($cmd);
}
