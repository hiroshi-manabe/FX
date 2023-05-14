#!/usr/bin/env perl
use strict;
use warnings;

use Config::Simple;

my $cfg = new Config::Simple('config.ini');
my $currency = $cfg->param('settings.currency_pair');
my @window_times = @{$cfg->param('settings.window_times')};
my @r_squared_values = @{$cfg->param('settings.r_squared_values')};

# Check if the command-line arguments are provided
if (@ARGV != 3) {
    print "Usage: perl script_name.pl <last_week> <training_weeks> <loop_iterations>\n";
    exit;
}

my $commands_file = "commands.txt";

my $last_week = $ARGV[0];
my $training_weeks = $ARGV[1];
my $loop_iterations = $ARGV[2];

my $root_directory = sprintf("./$currency/results_%02d", $last_week);

my $development_weeks = 1;

my $start_week = $last_week - $training_weeks - $loop_iterations - $development_weeks + 2;
my $end_week = $last_week - $training_weeks - $development_weeks + 1;

if ($start_week < 0) {
    print "Error: Start week cannot be negative. Please adjust the training_weeks and loop_iterations values.\n";
    exit;
}

open(my $fh, '>', $commands_file) or die "Could not open file '$commands_file' $!";

for my $window_time (@window_times) {
    for my $r_squared_value (@r_squared_values) {
        for (my $training_start_week = $start_week; $training_start_week <= $end_week; $training_start_week++) {
            my $training_end_week = $training_start_week + $training_weeks - 1;
            my $development_start_week = $training_end_week + 1;
            my $development_end_week = $training_end_week + $development_weeks;
            
            my $output_dir = sprintf("%s/%05d/%.4f/%02d", $root_directory, $window_time, $r_squared_value, $development_start_week);
            system("mkdir -p $output_dir");
            my $output_file = "$output_dir/result_all.txt";
            open IN, "<", $output_file;
            while (<IN>) {
            }
            for my $k(5..10) {
                for my $threshold(1..$k-1) {
                }
            }
        }
    }
}

close($fh);
