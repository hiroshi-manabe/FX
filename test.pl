#!/usr/bin/env perl
use strict;
use utf8;
use open IO => ":utf8", ":std";

use IO::Handle;
use List::Util qq(sum);

my $currency = "USDJPY";
my @in_file_list = qw(features.csv features_sell.csv);

my $delay = 3;
my $time_width = 60000;
my $min_count = 20;
my $min_profit = 5;

sub main {
    my $sell_flag = 0;
    if (@ARGV) {
        my $temp = shift @ARGV;
        $sell_flag = 1 if $temp eq "sell";
    }
    my $in_file = "$currency/$in_file_list[$sell_flag]";
    my ($sec, $min, $hour, $mday, $mon, $year, undef, undef, undef) = localtime(time);
    my $out_file = sprintf("$currency/test_result_%04d%02d%02d_%02d%02d%02d.txt", $year + 1900, $mon + 1, $mday, $hour, $min, $sec);
    
    open IN, "<", $in_file or die "$in_file: $!";
    my %features_all = ();
    while (<IN>) {
        chomp;
        my ($min_scale, $max_scale, $bits, $count, $result) = split/[\-,:]/;
        $features_all{$bits} = [$min_scale, $max_scale, $count, $result];
    }
    close IN;

    my @test_files;
    while (<$currency/weekly_past_data/week_*.csv>) {
        m{week_(\d{3})};
        next if $1 < 346;
        push @test_files, $_;
    }
    my @test_patterns;
    for (my $freq = 200; $freq <= 500; $freq += 30) {
        push @test_patterns, [$freq];

    }

    open OUT, ">", $out_file or die;
    OUT->autoflush;
    for my $test_pattern(@test_patterns) {
        print OUT "Test pattern: ".join(",", @{$test_pattern})."\n";
        my $score_all = 0;
        my $data_ref = filter_data(\%features_all, $test_pattern);
        if (scalar(keys %{$data_ref}) == 0) {
            print OUT join(",", 0, 0, 0)."\n";
            next;
        }
        for my $test_file(@test_files) {
            print "File: $test_file\n";
            my $score = 0;
            open IN, "<", $test_file or die "Cannot open: $test_file";
            my @data = ();
            my $prev_time = -99999;
            while (<IN>) {
                chomp;
                my @F = split/,/;
                push @data, [@F];
                next if scalar(@data) < $delay;
                my $time = $F[0];
                my $past = $data[-$delay-1]->[6];
                my ($scale, $bits) = split/:/, $past;
                if ($time >= $prev_time + $time_width and exists $data_ref->{$bits}) {
                    my ($min_scale, $max_scale, $count, $result) = @{$data_ref->{$bits}};
                    if ($scale >= $min_scale and $scale <= $max_scale) {
                        
                        my ($result, $result_time) = split/:/, $F[5];
                        print "Hit: bits $bits, max scale $max_scale, min scale $min_scale scale $scale result $result\n";
                        $score += $result;
                        $prev_time = $time;
                    }
                }
            }
            $score_all += $score;
        }
        print OUT join(",", $score_all)."\n";
    }
}

sub filter_data {
    my ($data_ref, $pattern) = @_;
    my ($freq_threshold) = @{$pattern};
    my $ret_ref = {};
    for my $key(keys %{$data_ref}) {
        my ($min_scale, $max_scale, $count, $result) = @{$data_ref->{$key}};
        $ret_ref->{$key} = [$min_scale, $max_scale, $count, $result] if $count >= $freq_threshold;
    }p
    return $ret_ref;
}

main();
