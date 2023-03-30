#!/usr/bin/env perl
use utf8;
use open qw(:std :utf8);
use autodie;
use Encode;
use strict;
use warnings;

use Config::Simple;

my $cfg = new Config::Simple('config.ini');
my $currency = $cfg->param('settings.currency_pair');

if (scalar(@ARGV) != 2) {
    print STDERR "$0 <start week> <end week>\n";
    exit(-1);
}

my ($start_week, $end_week) = @ARGV;
my @test_files;
while (<$currency/weekly_past_data/week_*.csv>) {
    m{week_(\d{3})};
    next unless $1 >= $start_week and $1 <= $end_week;
    push @test_files, $_;
}

my $past_width = 120000;
my $future_width = 30000;
my $count = 1;

open my $fh_out_result, ">", "$currency/past_data.txt";
my $week_num = 1;
for my $test_file(@test_files) {
    print STDERR "$test_file\n";
    print $fh_out_result "week $week_num\n";
    $week_num++;
    my @data;
    open my $fh, '<', $test_file;
    while (<$fh>) {
        chomp;
        my @F = split /,/;
        push @data, [@F];
    }
    close $fh;
    my $prev_time = 0;
    for my $i (0..$#data) {
        my @F = split/:/, $data[$i]->[6];
        my @coeffs = @F[1..3];
        my $fit = $F[4];
        my $result = (split/:/, $data[$i]->[5])[1];
        if (abs($coeffs[0]) < 3 and $fit > 0.94 and $data[$i]->[0] > $prev_time + $past_width + $future_width) {
            my $j = $i;
            $j-- while $data[$j]->[0] >= $data[$i]->[0] - $past_width and $j > 0;
            $j++;
            next if $i == $j or $past_width / ($i - $j) > 250;
            my $out_file = sprintf("temp/%03d.csv", $count);
            open my $fh_out, '>', $out_file;
            for (; $data[$j]->[0] <= $data[$i]->[0] + $future_width; ++$j) {
                print $fh_out join(",", @{$data[$j]}[0,1]) . "\n";
            }
            close $fh_out;
            print $fh_out_result join(",", @coeffs[1, 2], $result)."\n";
            $prev_time = $data[$i]->[0];
            $count++;
        }
    }
}
close $fh_out_result;

sub usage {
    die "Usage: $0 [options] file\n";
}
