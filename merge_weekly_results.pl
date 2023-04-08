#!/usr/bin/perl
use strict;
use warnings;

my $root_directory = "./results";

foreach my $window_time (60000, 120000, 180000, 240000, 300000) {
    foreach my $r_squared_value (map { 0.92 + $_ * 0.0025 } 0 .. 20) {
        foreach my $k_value (5 .. 10) {
            foreach my $threshold_value (1 .. $k_value - 1) {
                my $output_file = sprintf("%s/%05d/%.4f/result_%02d_%02d.txt", $root_directory, $window_time, $r_squared_value, $k_value, $threshold_value);
                open(my $combined_fh, '>', $output_file) or die "Could not open file '$output_file' $!";

                foreach my $training_start_week (1 .. 22) {
                    my $input_file = sprintf("%s/%05d/%.4f/%02d/result_%02d_%02d.txt", $root_directory, $window_time, $r_squared_value, $training_start_week, $k_value, $threshold_value);
                    open(my $input_fh, '<', $input_file) or die "Could not open file '$input_file' $!";
                    while (my $line = <$input_fh>) {
                        print $combined_fh $line;
                    }
                    close($input_fh);
                }
                close($combined_fh);
            }
        }
    }
}
