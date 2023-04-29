#!/usr/bin/env perl
use strict;
use warnings;

use Config::Simple;

my $cfg = new Config::Simple('config.ini');
my $currency = $cfg->param('settings.currency_pair');


# Check if the command-line arguments are provided
if (@ARGV != 2) {
    print "Usage: perl script_name.pl <training_weeks> <loop_iterations>\n";
    exit;
}

my $commands_file = "commands.txt";

my $training_weeks = $ARGV[0];
my $loop_iterations = $ARGV[1];

my $root_directory = sprintf("./$currency/results_%02d", $training_weeks);

my $development_weeks = 1;
my $last_week = 51;

my $start_week = $last_week - $training_weeks - $loop_iterations - $development_weeks + 2;
my $end_week = $last_week - $training_weeks - $development_weeks + 1;

if ($start_week < 0) {
    print "Error: Start week cannot be negative. Please adjust the training_weeks and loop_iterations values.\n";
    exit;
}

open(my $fh, '>', $commands_file) or die "Could not open file '$commands_file' $!";

foreach my $window_time (60000, 120000, 180000, 240000, 300000) {
    foreach my $r_squared_value (map { 0.92 + $_ * 0.0025 } 0 .. 20) {
        for (my $training_start_week = $start_week; $training_start_week <= $end_week; $training_start_week++) {
            my $training_end_week = $training_start_week + $training_weeks - 1;
            my $development_start_week = $training_end_week + 1;
            my $development_end_week = $training_end_week + $development_weeks;
            
            my $output_dir = sprintf("%s/%05d/%.4f/%02d", $root_directory, $window_time, $r_squared_value, $development_start_week);
            system("mkdir -p $output_dir");

            foreach my $k_value (5 .. 10) {
                foreach my $threshold_value (1 .. $k_value - 1) {
                    my $output_file = sprintf("%s/result_%02d_%02d.txt", $output_dir, $k_value, $threshold_value);
                    my $cmd = join(",", $training_start_week, $training_end_week, $development_start_week, $development_end_week, $k_value, $threshold_value, $window_time, $r_squared_value, $output_file);
                    print $fh "$cmd\n";
                }
            }
        }
    }
}

close($fh);
