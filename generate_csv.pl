#!/usr/bin/perl
use strict;
use warnings;
use utf8;
use open IO => ':utf8', ':std';
use List::Util qw(sum);
use Math::Trig;

my $root_directory = "./results";

sub factorial {
    my $n = shift;
    my $result = 1;

    for (my $i = 2; $i <= $n; $i++) {
        $result *= $i;
    }

    return $result;
}

sub double_factorial {
    my $n = shift;
    my $result = 1;

    for (my $i = $n % 2 == 0 ? 2 : 1; $i <= $n; $i += 2) {
        $result *= $i;
    }

    return $result;
}

sub gamma {
    my $x = shift;
    if ($x == int($x)) {
        return factorial($x - 1);
    } elsif ($x * 2 == int($x * 2)) {
        return sqrt(pi) * double_factorial(2 * $x - 2) / 2 ** ($x - 1);
    } else {
        die "Input is not an integer or half-integer.";
    }
}

foreach my $window_time (60000, 120000, 180000, 240000, 300000) {
    my $output_filename = "result_${window_time}.tsv";
    open my $output_file, ">", $output_filename or die "Cannot open $output_filename: $!";

    foreach my $r_squared_value (map { 0.92 + $_ * 0.0025 } 0 .. 20) {
        my %results;

        for my $threshold_value (1 .. 9) {
            for my $k_value (5 .. 10) {
                if ($threshold_value < $k_value) {
                    my @profits;
                    my $week = 0;

                    while ($week <= 21) {
                        my $file_path = sprintf("%s/%05d/%.4f/%02d/result_%02d_%02d.txt", $root_directory, $window_time, $r_squared_value, $week, $k_value, $threshold_value);
                        open my $file, "<", $file_path or die "Cannot open $file_path: $!";

                        while (my $line = <$file>) {
                            if ($line =~ /^利益: ([\d\.\-]+)/) {
                                push @profits, $1 - 8;
                            }
                        }

                        close $file;
                        $week++;
                    }

                    my $count = scalar @profits;
                    my ($average, $std_dev) = (0, 0);

                    if ($count > 1) {
                        my $n = $count;
                        my $correction_factor = 1;
                        if ($n < 30) {
                            $correction_factor = sqrt(2 / ($n - 1)) * gamma($n / 2) / gamma(($n - 1) / 2);
                        }
                        $average = sum(@profits) / $count;
                        my $variance = sum(map { ($_ - $average) ** 2 } @profits) / ($count - 1);
                        $std_dev = sqrt($variance) / $correction_factor;
                    }

                    my $key = sprintf("%.4f/%02d/%02d", $r_squared_value, $k_value, $threshold_value);
                    $results{$key} = [$count, $average, $std_dev];
                }
            }
        }

        foreach my $key (sort keys %results) {
            my ($count, $average, $std_dev) = @{$results{$key}};
            print $output_file "$key,$count,$average,$std_dev\n";
        }
    }

    close $output_file;
}
