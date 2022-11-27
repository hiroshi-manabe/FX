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
    my $out_file = sprintf("$currency/dev_result_%04d%02d%02d_%02d%02d%02d.txt", $year + 1900, $mon + 1, $mday, $hour, $min, $sec);
    print STDOUT "Output file: $out_file\n";
    
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
        next if $1 < 346 or $1 == 358;
        push @test_files, $_;
    }
    my @test_patterns;
    for (my $freq = 50; $freq <= 100; $freq += 10) {
        push @test_patterns, [$freq];

    }

    open OUT, ">", $out_file or die;
    OUT->autoflush;
    for my $test_pattern(@test_patterns) {
        print OUT "Test pattern: ".join(",", @{$test_pattern})."\n";
        my $hit_count_all = 0;
        my $score_all = 0;
        my $data_ref = filter_data(\%features_all, $test_pattern);
        my %score_by_feature = ();
        my %count_by_feature = ();
        if (scalar(keys %{$data_ref}) == 0) {
            print OUT join(",", 0, 0, 0)."\n";
            next;
        }
        for my $test_file(@test_files) {
            print OUT "File: $test_file\n";
            my $score = 0;
            my $hit_count = 0;
            open IN, "<", $test_file or die "Cannot open: $test_file";
            my @data = ();
            my $prev_time = -99999;
            while (<IN>) {
                chomp;
                my @F = split/,/;
                push @data, [@F];
                next if scalar(@data) <= $delay;
                my $time = $F[0];
                my $past = $data[-$delay-1]->[6];
                my ($scale, $bits) = split/:/, $past;
                if ($time >= $prev_time + $time_width and exists $data_ref->{$bits}) {
                    my ($min_scale, $max_scale, $count, $result) = @{$data_ref->{$bits}};
                    if ($scale >= $min_scale and $scale <= $max_scale) {
                        
                        my ($result, $result_time) = split/:/, $F[5];
                        print OUT "Hit: time $time bits $bits range $min_scale-$max_scale scale $scale result $result\n";
                        $score_by_feature{$bits} += $result;
                        $count_by_feature{$bits}++;
                        $hit_count++;
                        $score += $result;
                        $prev_time = $time;
                    }
                }
            }
            my $avr = 0;
            $avr = $score / $hit_count if $hit_count;
            print OUT "File total: score $score hit count $hit_count average score $avr\n";
            $hit_count_all += $hit_count;
            $score_all += $score;
            print OUT (("-" x 70)."\n");
        }
        my $avr_all = 0;
        $avr_all = $score_all / $hit_count_all if $hit_count_all;
        print OUT "Total: score $score_all hit count $hit_count_all average score $avr_all\n";
        for my $bits(keys %{$data_ref}) {
            my $score = $score_by_feature{$bits};
            my $count = $count_by_feature{$bits};
            my $avr = 0;
            $avr = $score / $count if $count;
            my ($min_scale, $max_scale, undef, $undef) = @{$data_ref->{$bits}};
            print OUT "$min_scale-$max_scale:$bits score $score count $count average $avr\n";
        }
        print OUT (("=" x 70)."\n");
    }
    close OUT;
}

sub filter_data {
    my ($data_ref, $pattern) = @_;
    my ($freq_threshold) = @{$pattern};
    my $ret_ref = {};
    for my $key(keys %{$data_ref}) {
        my ($min_scale, $max_scale, $count, $result) = @{$data_ref->{$key}};
        $ret_ref->{$key} = [$min_scale, $max_scale, $count, $result] if $count >= $freq_threshold;
    }
    return $ret_ref;
}

main();
