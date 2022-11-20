#!/usr/bin/env perl
use strict;
use utf8;
use open IO => ":utf8", ":std";

my @currency_list = qw(USDJPY);

sub main() {
    my $currency = "USDJPY";
    my @ticks_to_look_list = (50, 100, 200);
    while (<$currency/weekly/*.csv>) {
        open IN, "<", $_ or die;
        my @data_all = ();
        while (<IN>) {
            chomp;
            my ($time, $ask, undef, undef, undef) = split/,/;
            push @data_all, [$time, $ask];
            for my $ticks_to_look(@ticks_to_look_list) {
                next if scalar(@data_all) < $ticks_to_look * 1.5;
                
            }
        }
    }
}

sub calculate_gradient {
    my ($array_ref, $start_pos, $count) = @_;
    my ($x_sum, $y_sum);
    for (my $i = 0; $i < $count; ++$i) {
        $x_sum += $array_ref[$start_pos + $i]->[0];
        $y_sum += $array_ref[$start_pos + $i]->[1];
    }
    my ($x_avr, $y_avr) = ($x_sum / $count, $y_sum / $count);
    
}

main();

