#!/usr/bin/env perl
use strict;
use utf8;
use open IO => ":utf8", ":std";

open FIND, "-|", qq{find . -name "*.bi5" -depth 5};
while (<FIND>) {
    chomp;
    my $bi5_file = $_;
    my $bin_file = $bi5_file;
    $bin_file =~ s{\.bi5$}{.bin};
    if (not -f $bin_file) {
        my $cmd = (-s $bi5_file) ? qq{lzma -kdc -S bi5 $bi5_file > $bin_file} : qq{touch $bin_file};
        print $cmd."\n";
        system $cmd;
    }
    my $csv_file = $bi5_file;
    $csv_file =~ s{\.bi5$}{.csv};
    if (not -f $csv_file) {
        my $cmd = (-s $bin_file) ?  qq{./bin_to_csv $bin_file > $csv_file} : qq{touch $csv_file};
        print $cmd."\n";
        system $cmd;
    }
}
