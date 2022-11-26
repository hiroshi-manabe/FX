#!/usr/bin/env perl
use strict;
use utf8;
use open IO => ":utf8", ":std";

use IO::Handle;
use List::Util qq(sum);

my ($sec, $min, $hour, $mday, $mon, $year, undef, undef, undef) = localtime(time);

my $currency = "USDJPY";
my $in_file = "$currency/stat.csv";
my $out_file = sprintf("$currency/test_result_%04d%02d%02d_%02d%02d%02d.txt", $year + 1900, $mon + 1, $mday, $hour, $min, $sec);

my $lag = 3;
my $time_width = 60000;
my $min_count = 20;
my $min_profit = 5;

sub main {
    open IN, "<", $in_file or die "Cannot open: $in_file";
    my @data_all = ();
    while (<IN>) {
        chomp;
        my @F = split/[,:]/;
        push @data_all, [@F];
    }
    close IN;

    my $processed_data = process_data(\@data_all, $min_count, $min_profit);
    
    if (@ARGV == 2) {
        my $output_freq;
        my $output_count;
        ($output_freq, $output_count) = @ARGV;
        my $output_ref = filter_data($processed_data, [$output_freq, $output_count]);
        for my $key(keys %{$output_ref}) {
            print join(",", $key)."\n";
        }
        exit(0);
    }
    
    my @test_files;
    while (<$currency/weekly_past_data/week_*.csv>) {
        m{week_(\d{3})};
        next if $1 < 346;
        push @test_files, $_;
    }
    my @test_patterns;
    for (my $freq = 200; $freq <= 500; $freq += 30) {
        for (my $feature_count = 2; $feature_count <= 10; $feature_count += 2) {
            push @test_patterns, [$freq, $feature_count];

        }
    }

    open OUT, ">", $out_file or die;
    OUT->autoflush;
    for my $test_pattern(@test_patterns) {
        print OUT join(",", @{$test_pattern})."\n";
        my $score_all = 0;
        my $data_ref = filter_data($processed_data, $test_pattern);
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
                next if scalar(@data) < $lag;
                my $time = $F[0];
                my $past = $data[-$lag]->[6];
                my ($scale, $bits) = split/:/, $past;
                if ($time >= $prev_time + $time_width and exists $data_ref->{$bits}) {
                    my ($result, $result_time) = split/:/, $F[5];
                    push @scores, $result;
                    $feature_dict{$bits} += $result;
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
    my ($freq_threshold, $feature_count) = @{$pattern};
    my %temp_sum_dict = ();
    my %temp_freq_dict = ();
    for my $key(keys %{$data_ref}) {
        my (undef, $bits) = split/:/, $key;
        for my $t(@{$data_ref->{$key}}) {
            my ($result, undef) = @{$t};
            $temp_sum_dict{$bits} += $result;
            $temp_freq_dict{$bits}++;
        }
    }
    my %temp_avr_dict = ();
    for my $key(keys %temp_freq_dict) {
        next if $temp_freq_dict{$key} < $freq_threshold;
        $temp_avr_dict{$key} = $temp_sum_dict{$key} / $temp_freq_dict{$key};
    }
    my $count = 0;
    my $ret_ref = {};
    for my $key(sort {$temp_avr_dict{$b} <=> $temp_avr_dict{$a} } keys %temp_avr_dict) {
        $ret_ref->{$key} = $temp_avr_dict{$key};
        $count++;
        last if $count >= $feature_count;
    }
    return $ret_ref;
}

sub process_data {
    my ($data_all_ref, $min_count, $min_profit) = @_;
    my $ret_ref = {};
    my $sum;
    my $count;
    my %sum_dict;
    my %count_dict;
    my $prev_bits;
    for my $data_ref(@{$data_all_ref}, [0, "", "", 0]) {
        my ($scale, $bits, $result, undef) = @{$data_ref};
        if ($prev_bits ne "" and $bits ne $prev_bits) {
            my $count_all = sum(map { $count_dict{$_} } keys %count_dict);
            if ($count_all >= $min_count) {
                my %sum_count_dict;
                my $has_profit = 0;
                for my $s(keys %sum_dict) {
                    $sum_count_dict{$s} = [$sum_dict{$s}, $count_dict{$s}];
                    $has_profit = 1 if $sum_dict{$s} / $count_dict{$s} >= $min_profit;
                }
                if ($has_profit) {
                    my @scale_list = sort {$a<=>$b} keys %sum_count_dict;
                    my @best_params;
                    my $best_profit = 0;
                    for (my $i = 0; $i < scalar(@scale_list); ++$i) {
                        for (my $j = $i + 1; $j <= scalar(@scale_list); ++$j) {
                            my $profit = sum(map { $_->[0]; } @sum_count_dict{@scale_list[$i..$j-1]});
                            my $count = sum(map { $_->[1]; } @sum_count_dict{@scale_list[$i..$j-1]});
                            next if $profit / $count < $min_profit;
                            if ($profit > $best_profit) {
                                $best_profit = $profit;
                                @best_params = ($scale_list[$i], $scale_list[$j-1], $count);
                            }
                        }
                    }
                    $ret_ref->{$prev_bits} = [@best_params] if $best_profit > 0;
                }
            }
            %sum_dict = ();
            %count_dict = ();
            $count_all = 0;
        }
        $sum_dict{$scale} += $result;
        $count_dict{$scale}++;
        $prev_bits = $bits;
    }
    return $ret_ref;
}

main();
