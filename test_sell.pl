#!/usr/bin/env perl
use strict;
use utf8;
use open IO => ":utf8", ":std";

use IO::Handle;
use Statistics::Distributions;

my $in_file = "USDJPY/stat_sell.csv";
my $out_file = "USDJPY/test_sell_result.txt";

my $lag = 3;
my $time_width = 320000;

sub main {
    open IN, "<", $in_file or die "Cannot open: $in_file";
    my %data_all = ();
    while (<IN>) {
        chomp;
        my @F = split/,/;
        push @{$data_all{$F[0]}}, [$F[1], $F[2]];
    }
    close IN;

    if (@ARGV == 2) {
        my $output_freq;
        my $output_count;
        ($output_freq, $output_count) = @ARGV;
        my $output_ref = filter_data(\%data_all, [$output_freq, $output_count]);
        for my $key(keys %{$output_ref}) {
            print join(",", $key)."\n";
        }
        exit(0);
    }
    
    my @test_files = qw(
        USDJPY/weekly_past_sell_data/week_522_20220002.csv
        USDJPY/weekly_past_sell_data/week_523_20220009.csv
        USDJPY/weekly_past_sell_data/week_524_20220016.csv
        USDJPY/weekly_past_sell_data/week_525_20220023.csv
        USDJPY/weekly_past_sell_data/week_526_20220030.csv
        USDJPY/weekly_past_sell_data/week_527_20220106.csv
        USDJPY/weekly_past_sell_data/week_528_20220113.csv
        USDJPY/weekly_past_sell_data/week_529_20220120.csv
        USDJPY/weekly_past_sell_data/week_530_20220127.csv
        USDJPY/weekly_past_sell_data/week_531_20220206.csv
        USDJPY/weekly_past_sell_data/week_532_20220213.csv
        USDJPY/weekly_past_sell_data/week_533_20220220.csv
        USDJPY/weekly_past_sell_data/week_534_20220227.csv
        USDJPY/weekly_past_sell_data/week_535_20220303.csv
        USDJPY/weekly_past_sell_data/week_536_20220310.csv
        USDJPY/weekly_past_sell_data/week_537_20220317.csv
        USDJPY/weekly_past_sell_data/week_538_20220324.csv
        USDJPY/weekly_past_sell_data/week_539_20220401.csv
        USDJPY/weekly_past_sell_data/week_540_20220408.csv
        USDJPY/weekly_past_sell_data/week_541_20220415.csv
        USDJPY/weekly_past_sell_data/week_542_20220422.csv
        USDJPY/weekly_past_sell_data/week_543_20220429.csv
        USDJPY/weekly_past_sell_data/week_544_20220505.csv
        USDJPY/weekly_past_sell_data/week_545_20220512.csv
        USDJPY/weekly_past_sell_data/week_546_20220519.csv
        USDJPY/weekly_past_sell_data/week_547_20220526.csv
        USDJPY/weekly_past_sell_data/week_548_20220603.csv
        USDJPY/weekly_past_sell_data/week_549_20220610.csv
        USDJPY/weekly_past_sell_data/week_550_20220617.csv
        USDJPY/weekly_past_sell_data/week_551_20220624.csv
        USDJPY/weekly_past_sell_data/week_552_20220631.csv
        USDJPY/weekly_past_sell_data/week_553_20220707.csv
        USDJPY/weekly_past_sell_data/week_554_20220714.csv
        USDJPY/weekly_past_sell_data/week_555_20220721.csv
        USDJPY/weekly_past_sell_data/week_556_20220728.csv
        USDJPY/weekly_past_sell_data/week_557_20220804.csv
        USDJPY/weekly_past_sell_data/week_558_20220811.csv
        USDJPY/weekly_past_sell_data/week_559_20220818.csv
        USDJPY/weekly_past_sell_data/week_560_20220825.csv
        USDJPY/weekly_past_sell_data/week_561_20220902.csv
        USDJPY/weekly_past_sell_data/week_562_20220909.csv
        USDJPY/weekly_past_sell_data/week_563_20220916.csv
        USDJPY/weekly_past_sell_data/week_564_20220923.csv
        USDJPY/weekly_past_sell_data/week_565_20220930.csv
        USDJPY/weekly_past_sell_data/week_566_20221006.csv
        );
    my @test_patterns;
    for (my $log_time_threshold = 15.0; $log_time_threshold <= 17.0; $log_time_threshold += 0.5) {
        for (my $freq = 14; $freq <= 24; $freq += 2) {
            for (my $feature_count = 10; $feature_count <= 26; $feature_count += 2) {
                push @test_patterns, [$freq, $feature_count, $log_time_threshold];
            }
        }
    }

    open OUT, ">", $out_file or die;
    OUT->autoflush;
    for my $test_pattern(@test_patterns) {
        print OUT join(",", @{$test_pattern})."\n";
        my ($plus, $minus) = (0, 0);
        my $data_ref = filter_data(\%data_all, $test_pattern);
        if (scalar(keys %{$data_ref}) == 0) {
            print OUT join(",", 0, 0, 0)."\n";
            next;
        }
        for my $test_file(@test_files) {
            my ($p, $m) = (0, 0);
            open IN, "<", $test_file or die "Cannot open: $test_file";
            my @data = ();
            my $prev_time = -99999;
            while (<IN>) {
                chomp;
                my @F = split/,/;
                push @data, [@F];
                my $time = $F[0];
                if (scalar(@data) > $lag and $time >= $prev_time + $time_width and exists $data_ref->{$data[-$lag]->[7]}) {
                    if ($F[5] eq "+") {
                        $p++;
                    }
                    elsif ($F[5] eq "-") {
                        $m++;
                    }
                    $prev_time = $time;
                }
            }
            print OUT join(",", $test_file, $p, $m, $p - $m)."\n";
            $plus += $p;
            $minus += $m;
        }
        print OUT join(",", $plus, $minus, $plus - $minus)."\n";
    }
}

sub filter_data {
    my ($data_ref, $pattern) = @_;
    my ($freq, $feature_count, $log_time_threshold) = @{$pattern};
    my $temp_ref = {};
    for my $key(keys %{$data_ref}) {
        my $plus = 0;
        my $minus = 0;
        my $all = 0;
        my $log_plus_time_sum = 0;
        for my $ref(@{$data_ref->{$key}}) {
            if ($ref->[0] eq "+") {
                ++$plus;
                $log_plus_time_sum += log($ref->[1]);
            }
            else {
                ++$minus;
            }
        }
        next if $plus == 0;
        my $log_plus_time_avr = $log_plus_time_sum / $plus;
        $all = $plus + $minus;
        $temp_ref->{$key} = $plus / $all if $plus > $minus and $all > $freq and $log_plus_time_avr < $log_time_threshold;
    }
    my $count;
    my $ret_ref = {};
    for my $key(sort {$temp_ref->{$b} <=> $temp_ref->{$a} } keys %{$temp_ref}) {
        $ret_ref->{$key} = $temp_ref->{$key};
        $count++;
        last if $count > $feature_count;
    }
    return $ret_ref;
}

main();
