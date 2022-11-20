use strict;
use utf8;

open IN, "<", "minutes.txt";

my @data;
my $all;
while (<IN>) {
    chomp;
    my @F = split/,/;
    if (not $_) {
        @data = ();
    }
    else {
        push @data, [@F];
        next if @data < 60;
        if ($data[-2]->[1] - $data[-3]->[1] < 10) {
            my $diff =  $data[-1]->[1] - $data[-2]->[1] - 2;
            $all += $diff;
            print "$diff,$all\n";
        }
    }
}
