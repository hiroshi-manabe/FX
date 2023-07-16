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
    }
    elsif ($x * 2 == int($x * 2)) {
        return sqrt(pi) * double_factorial(2 * $x - 2) / 2 ** ($x - 1);
    }
    else {
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
my $commission = $cfg->param('settings.commission');
my @window_times = @{$cfg->param('settings.window_times')};
my @r_squared_values = @{$cfg->param('settings.r_squared_values')};
my $k_value = $cfg->param('settings.k_value');

for my $window_time (@window_times) {
    my $root_directory = "./$currency";
    my $output_directory = sprintf("${root_directory}/results_%02d", $last_week);
    mkdir $output_directory if not -d $output_directory;
    my $output_filename = sprintf("${root_directory}/results_%02d/${window_time}.csv", $last_week);
    open my $output_file, ">", $output_filename or die "Cannot open $output_filename: $!";

    for my $r_squared_value (@r_squared_values) {
        my %results;
        my $lines_all = 0;

        for my $week($last_week - 19 .. $last_week) {
            my $file_path = sprintf("%s/%02d/%05d/%.4f.txt", $root_directory, $week, $window_time, $r_squared_value);
            my $lines_file_path = sprintf("%s/%02d/%05d/%.4f_lines.txt", $root_directory, $week, $window_time, $r_squared_value);
            open my $fp_lines_in, "<", $lines_file_path or die "Cannot open $lines_file_path: $!";
            my $lines = <$fp_lines_in>;
            chomp $lines;
            close $fp_lines_in;
            next if $lines < 200;
                        
            open my $fp_in, "<", $file_path or die "Cannot open $file_path: $!";
            while (my $line = <$fp_in>) {
                chomp $line;
                my ($index, $coef1, $coef2, $knn_results, $profit_buy, $profit_sell) = split /,/, $line;
                my %knn_results = map { my ($k, @values) = split /\//; $k => \@values } split /:/, $knn_results;

                for my $threshold_value (1 .. 9) {
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
                        $profit -= $commission;
                        $profit = 50 if $profit > 50; # outlier
                        my $key = sprintf("%.4f/%02d/%02d", $r_squared_value, $k_value, $threshold_value);
                        push @{$results{$key}}, $profit;
                   }
                }
            }
            close $fp_in;
        }

        for my $key (sort keys %results) {
            my ($r_squared_value, undef, undef) = split m{/}, $key;
            
            my @profits = @{$results{$key}};
            my $count = scalar @profits;
            my ($average, $std_dev) = (0, 0);

#            my $n = $count;
#            my $correction_factor = 1;
#            if ($n < 30) {
#                $correction_factor = sqrt(2 / ($n - 1)) * gamma($n / 2) / gamma(($n - 1) / 2);
#            }
            $average = sum(@profits) / $count;
#            my $variance = sum(map { ($_ - $average) ** 2 } @profits) / ($count - 1);
#            $std_dev = sqrt($variance) / $correction_factor;
            print $output_file "$key,$count,$average,$std_dev\n";
        }
    }

    close $output_file;
}
