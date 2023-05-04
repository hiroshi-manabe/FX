#!/usr/bin/env perl
use strict;
use utf8;
use open IO => ':utf8', ':std';

sub printex {
    my $cmd = shift;
    print "$cmd\n";
    system $cmd;
}

for my $i(40..51) {
    my $j = $i - 1;
    my $k = $i - 20;
    my $cmd;
    $cmd = qq{./generate_csv.pl $j};
    printex($cmd);
    my $params_path = qq{USDJPY/results_$j/params.csv};
    $cmd = qq{./find_optimal.py $j | ./report_to_params.pl > $params_path};
    printex($cmd);
    open IN, "<", $params_path or die "$params_path $!";
    while (<IN>) {
        chomp;
        my @F = split/,/;
        $cmd = qq{./test.py $k $j $i $i --k_value $F[2] --threshold $F[3] --window_time $F[0] --r_squared_value $F[1]};
        printex($cmd);
    }
}
