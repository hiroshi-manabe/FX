#!/usr/bin/env perl

use strict;
use warnings;

my $best_training_weeks;
my @results;

while (my $line = <>) {
    if ($line =~ /^Best result for last_week (\d+), window_time (\d+): Label ([\d.]+)\/(\d+)\/(\d+), .* Final_f ([\d.]+)/) {
        my ($training_weeks, $window_time, $label, $label_part_1, $label_part_2, $final_f) = ($1, $2, $3, $4, $5, $6);

        push @results, {
            training_weeks => $training_weeks,
            window_time    => $window_time,
            label          => $label,
            label_part_1   => $label_part_1,
            label_part_2   => $label_part_2,
            final_f        => $final_f
        };
    }
}

for my $result (@results) {
    print "$result->{window_time},$result->{label},$result->{label_part_1},$result->{label_part_2},$result->{final_f}\n";
}
