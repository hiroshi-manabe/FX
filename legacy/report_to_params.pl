#!/usr/bin/env perl

use strict;
use warnings;

my $best_training_weeks;
my @results;

while (my $line = <>) {
    if ($line =~ /^Best result for last_week (\d+), window_time (\d+): Label ([\d.]+)\/(\d+)\/(\d+), .* Final_f (.+)/) {
        my ($training_weeks, $window_time, $r_squared_value, $k_value, $threshold_value, $final_f) = ($1, $2, $3, $4, $5, $6);

        push @results, {
            training_weeks  => $training_weeks,
            window_time     => $window_time,
            r_squared_value => $r_squared_value,
            k_value         => $k_value - 0,
            threshold_value => $threshold_value - 0,
            final_f         => $final_f
        };
    }
}

for my $result (@results) {
    print "$result->{window_time},$result->{r_squared_value},$result->{k_value},$result->{threshold_value},$result->{final_f}\n";
}
