#!/usr/bin/env perl
use strict;
use warnings;
use utf8;
use open IO => ':utf8', ':std';

use Config::Simple;

if (@ARGV != 1) {
    print "Usage: perl script_name.pl <last_week>\n";
    exit;
}

my $last_week = shift @ARGV;

my $cfg = new Config::Simple('config.ini');
my $currency = $cfg->param('settings.currency_pair');
my @window_times = @{$cfg->param('settings.window_times')};
my @r_squared_values = @{$cfg->param('settings.r_squared_values')};


for my $window_time (@window_times) {
    my $root_directory = sprintf("./$currency/results_%02d", $last_week);
    my $output_filename = "${root_directory}/${window_time}.md";
    open my $output_file, ">", $output_filename or die "Cannot open $output_filename: $!";
    my %results;

    for my $r_squared_value (@r_squared_values) {
        print $output_file "## $window_time / $r_squared_value\n\n";
        print $output_file "| Threshold \ K | 5 | 6 | 7 | 8 | 9 | 10 |\n";
        print $output_file "|--------------|---|---|---|---|---|----|\n";
        for my $week($last_week - 19 .. $last_week) { 
            my $file_path = sprintf("%s/%05d/%.4f/%02d.txt", $root_directory, $window_time, $r_squared_value, $week);
            open my $file, "<", $file_path or die "Cannot open $file_path: $!";
            while (my $line = <$file>) {
                chomp $line;
                my ($index, $coef1, $coef2, $knn_results, $profit_buy, $profit_sell) = split /,/, $line;
                my %knn_results = map { my ($k, @values) = split /\//; $k => \@values } split /:/, $knn_results;
            

                for my $threshold_value (1 .. 9) {
                    for my $k_value (5 .. 10) {
                        if ($threshold_value < $k_value) {
                            my $action = "pass";  # default action
                            if (abs($knn_results{$k_value}->[0]) >= $threshold_value) {
                                $action = "buy";
                            }
                            elsif (abs($knn_results{$k_value}->[1]) >= $threshold_value) {
                                $action = "sell";
                            }
                            next if $action eq "pass";
                            my $profit;
                            if ($action eq "sell") {
                                $profit = $profit_sell;
                            }
                            elsif ($action eq "buy") {
                                $profit = $profit_buy;
                            }
                            $profit -= 5; # commission
                            $profit = 50 if $profit > 50; # outlier
                            my $key = sprintf("%.4f/%02d/%02d", $r_squared_value, $k_value, $threshold_value);
                            $results{$key} += $profit;
                        }
                    }
                }
            }
        }
        for my $threshold_value(1..9) {
            print $output_file "| $threshold_value ";
            for my $k_value (5 .. 10) {
                if ($threshold_value < $k_value) {
                    my $key = sprintf("%.4f/%02d/%02d", $r_squared_value, $k_value, $threshold_value);
                    printf $output_file "| %+.1f ", exists $results{$key} ? $results{$key} : 0;
                }
                else {
                    print $output_file "| - ";
                }
            }
            print $output_file "|\n";
        }
        print $output_file "\n";
    }

    my @top_results = sort { $results{$b} <=> $results{$a} } keys %results;
    @top_results = @top_results[0..2];
    print $output_file "### Top 3 Results:\n\n";
    for my $key (@top_results) {
        my ($r_squared, $k, $threshold) = split("/", $key);
        print $output_file "* R-Squared: $r_squared, K: $k, Threshold: $threshold, Profit: $results{$key}\n";
    }

    close $output_file;
}
