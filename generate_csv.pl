#!/usr/bin/env perl
use strict;
use warnings;
use utf8;
use open IO => ':utf8', ':std';
use Config::Simple;
use List::Util qw(sum);
use Math::Trig;

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
    my $output_filename = "${root_directory}/${window_time}.csv";
    open my $output_file, ">", $output_filename or die "Cannot open $output_filename: $!";

    for my $r_squared_value (@r_squared_values) {
        my %results;

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
                            } elsif (abs($knn_results{$k_value}->[1]) >= $threshold_value) {
                                $action = "sell";
                            }
                            next if $action eq "pass";
                            
                            my $profit;
                            if ($action eq "sell") {
                                $profit = $profit_sell;
                            } elsif ($action eq "buy") {
                                $profit = $profit_buy;
                            }
                            $profit -= 8; # commission
                            $profit = 50 if $profit > 50; # outliers
                            my $key = sprintf("%.4f/%02d/%02d", $r_squared_value, $k_value, $threshold_value);
                            push @{$results{$key}}, $profit;
                        }
                    }
                }
            }
        }

        for my $key (sort keys %results) {
            my @profits = @{$results{$key}};
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

            print $output_file "$key,$count,$average,$std_dev\n";
        }
    }

    close $output_file;
}
