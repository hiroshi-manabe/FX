#!/usr/bin/perl
use strict;
use warnings;
use utf8;
use open IO => ':utf8', ':std';

my $root_directory = "./results";

foreach my $window_time (60000, 120000, 180000, 240000, 300000) {
    my $output_filename = "result_${window_time}.md";
    open my $output_file, ">", $output_filename or die "Cannot open $output_filename: $!";
    my %results;

    foreach my $r_squared_value (map { 0.92 + $_ * 0.0025 } 0 .. 20) {
        print $output_file "## $window_time / $r_squared_value\n\n";
        print $output_file "| Threshold \ K | 5 | 6 | 7 | 8 | 9 | 10 |\n";
        print $output_file "|--------------|---|---|---|---|---|----|\n";

        for my $threshold_value (1 .. 9) {
            print $output_file "| $threshold_value ";

            for my $k_value (5 .. 10) {
                if ($threshold_value < $k_value) {
                    my $total_profit = 0;
                    my $week = 1;

                    while ($week <= 22) {
                        my $file_path = sprintf("%s/%05d/%.4f/%02d/result_%02d_%02d.txt", $root_directory, $window_time, $r_squared_value, $week, $k_value, $threshold_value);
                        open my $file, "<", $file_path or die "Cannot open $file_path: $!";

                        while (my $line = <$file>) {
                            if ($line =~ /利益: ([\d\.\-]+)/) {
                                $total_profit += $1 - 5;
                            }
                        }

                        close $file;
                        $week++;
                    }

                    printf $output_file "| %+.1f ", $total_profit;
                    $results{"$r_squared_value $k_value $threshold_value"} = $total_profit;
                } else {
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
        my ($r_squared, $k, $threshold) = split(" ", $key);
        print $output_file "* R-Squared: $r_squared, K: $k, Threshold: $threshold, Profit: $results{$key}\n";
    }

    close $output_file;
}
