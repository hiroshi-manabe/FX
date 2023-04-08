#!/usr/bin/perl
use strict;
use warnings;

my $make_past_data_script = "./make_past_data.py";
my $test_script = "./test.py";
my $root_directory = "./results";

foreach my $window_time (60000, 120000, 180000, 240000, 300000) {
    foreach my $r_squared_value (map { 0.92 + $_ * 0.0025 } 0 .. 20) {
        my $cmd = "python3 $make_past_data_script 0 50 --window_time $window_time --r_squared_value $r_squared_value";
        print "$cmd\n";
        system($cmd);
        
        my $training_start_week = 1;
        while ($training_start_week <= 22) {
            my $output_dir = sprintf("%s/%05d/%.4f/%02d", $root_directory, $window_time, $r_squared_value, $training_start_week);
            system("mkdir -p $output_dir");

            foreach my $k_value (5 .. 10) {
                foreach my $threshold_value (1 .. $k_value - 1) {
                    my $output_file = sprintf("%s/result_%02d_%02d.txt", $output_dir, $k_value, $threshold_value);
                    my $cmd2 = "python3 $test_script $training_start_week " . ($training_start_week + 28) . " " . ($training_start_week + 29) . " " . ($training_start_week + 29) . " --k_value $k_value --threshold_value $threshold_value > $output_file";
                    print "$cmd2\n";
                    system($cmd2);
                }
            }

            $training_start_week++;
        }
    }
}
