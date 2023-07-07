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
for my $i(39..59) {
    $cmd = qq{./generate_csv.pl $i};
    print OUT "$cmd\n";
}
$cmd = qq{parallel -j 8 :::: commands.txt};
printex($cmd);
close OUT;

for my $i(39..59) {
    my $k = $i - 20;
    my $params_path = qq{$currency/results_$i/params.csv};
    $cmd = qq{./find_optimal.py $i > $params_path};
    printex($cmd);
}
