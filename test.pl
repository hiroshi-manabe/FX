#!/usr/bin/env perl
use strict;
use utf8;
use open IO => ":utf8", ":std";

use IO::Handle;
use Statistics::Distributions;

my ($sec, $min, $hour, $mday, $mon, $year, undef, undef, undef) = localtime(time);

my $in_file = "USDJPY/stat.csv";
my $out_file = sprintf("USDJPY/test_result_%04d%02d%02d_%02d%02d%02d.txt", $year + 1900, $mon + 1, $mday, $hour, $min, $sec);

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
        USDJPY/weekly_past_data/week_522_20220002.csv
        USDJPY/weekly_past_data/week_523_20220009.csv
        USDJPY/weekly_past_data/week_524_20220016.csv
        USDJPY/weekly_past_data/week_525_20220023.csv
        USDJPY/weekly_past_data/week_526_20220030.csv
        USDJPY/weekly_past_data/week_527_20220106.csv
        USDJPY/weekly_past_data/week_528_20220113.csv
        USDJPY/weekly_past_data/week_529_20220120.csv
        USDJPY/weekly_past_data/week_530_20220127.csv
        USDJPY/weekly_past_data/week_531_20220206.csv
        USDJPY/weekly_past_data/week_532_20220213.csv
        USDJPY/weekly_past_data/week_533_20220220.csv
        USDJPY/weekly_past_data/week_534_20220227.csv
        USDJPY/weekly_past_data/week_535_20220303.csv
        USDJPY/weekly_past_data/week_536_20220310.csv
        USDJPY/weekly_past_data/week_537_20220317.csv
        USDJPY/weekly_past_data/week_538_20220324.csv
        USDJPY/weekly_past_data/week_539_20220401.csv
        USDJPY/weekly_past_data/week_540_20220408.csv
        USDJPY/weekly_past_data/week_541_20220415.csv
        USDJPY/weekly_past_data/week_542_20220422.csv
        USDJPY/weekly_past_data/week_543_20220429.csv
        USDJPY/weekly_past_data/week_544_20220505.csv
        USDJPY/weekly_past_data/week_545_20220512.csv
        USDJPY/weekly_past_data/week_546_20220519.csv
        USDJPY/weekly_past_data/week_547_20220526.csv
        USDJPY/weekly_past_data/week_548_20220603.csv
        USDJPY/weekly_past_data/week_549_20220610.csv
        USDJPY/weekly_past_data/week_550_20220617.csv
        USDJPY/weekly_past_data/week_551_20220624.csv
        USDJPY/weekly_past_data/week_552_20220631.csv
        USDJPY/weekly_past_data/week_553_20220707.csv
        USDJPY/weekly_past_data/week_554_20220714.csv
        USDJPY/weekly_past_data/week_555_20220721.csv
        USDJPY/weekly_past_data/week_556_20220728.csv
        USDJPY/weekly_past_data/week_557_20220804.csv
        USDJPY/weekly_past_data/week_558_20220811.csv
        USDJPY/weekly_past_data/week_559_20220818.csv
        USDJPY/weekly_past_data/week_560_20220825.csv
        USDJPY/weekly_past_data/week_561_20220902.csv
        USDJPY/weekly_past_data/week_562_20220909.csv
        USDJPY/weekly_past_data/week_563_20220916.csv
        USDJPY/weekly_past_data/week_564_20220923.csv
        USDJPY/weekly_past_data/week_565_20220930.csv
        USDJPY/weekly_past_data/week_566_20221006.csv
        );
    my @test_patterns;
    for (my $freq = 10; $freq <= 30; $freq += 10) {
        for (my $feature_count = 4; $feature_count <= 10; $feature_count += 2) {
            push @test_patterns, [$freq, $feature_count];

        }
    }

    open OUT, ">", $out_file or die;
    OUT->autoflush;
    for my $test_pattern(@test_patterns) {
        print OUT join(",", @{$test_pattern})."\n";
        my $score_all = 0;
        my $data_ref = filter_data(\%data_all, $test_pattern);
        if (scalar(keys %{$data_ref}) == 0) {
            print OUT join(",", 0, 0, 0)."\n";
            next;
        }
        my %feature_dict = ();
        for my $test_file(@test_files) {
            my $score = 0;
            open IN, "<", $test_file or die "Cannot open: $test_file";
            my @data = ();
            my @scores = ();
            my $prev_time = -99999;
            while (<IN>) {
                chomp;
                my @F = split/,/;
                push @data, [@F];
                my $time = $F[0];
                if (scalar(@data) > $lag and $time >= $prev_time + $time_width and exists $data_ref->{$data[-$lag]->[6]}) {
                    my ($result, $result_time) = split/:/, $F[5];
                    push @scores, $result;
                    $feature_dict{$data[-$lag]->[6]} += $result;
                    $score += $result;
                    $prev_time = $time;
                }
            }
            print OUT join(",", $test_file, $score, join("/", @scores))."\n";
            $score_all += $score;
        }
        for my $feature(keys %feature_dict) {
            print OUT join(":", $feature, $feature_dict{$feature})."\n";
        }
        print OUT join(",", $score_all)."\n";
    }
}

sub filter_data {
    my ($data_ref, $pattern) = @_;
    my ($freq, $feature_count) = @{$pattern};
    my $temp_ref = {};
    for my $key(keys %{$data_ref}) {
        my $sum = 0;
        my $count = scalar(@{$data_ref->{$key}});
        next if $count == 0;
        for my $ref(@{$data_ref->{$key}}) {
            $sum += $ref->[0];
        }
        next if $sum < 0;;
        $temp_ref->{$key} = [$sum / $count, $count];
    }
    my $count = 0;
    my $ret_ref = {};
    for my $key(sort {$temp_ref->{$b}->[0] <=> $temp_ref->{$a}->[0] } keys %{$temp_ref}) {
        if ($temp_ref->{$key}->[1] >= $freq) {
            $ret_ref->{$key} = $temp_ref->{$key};
            $count++;
            last if $count >= $feature_count;
        }
    }
    return $ret_ref;
}

main();
