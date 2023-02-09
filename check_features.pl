#!/usr/bin/env perl

use strict;
use utf8;
use open IO => ":utf8", ":std";
use IO::Handle;

my $score_threshold = 7;
my $delay = 3;
my $result_time_key = 60000;
my $speed_threshold = 1000;
my $speed_wait = 600000;
my $order_wait = 300000;

sub main {
    my $input_filename = "stat3.csv";
    my $output_filename = "to_check.txt";
    
    my $currency;
    while (<currency_??????>) {
        m{currency_(.{6})};
        $currency = $1;
    }

    if (scalar(@ARGV) != 3) {
        print STDERR "$0 <week 1> <week 2> <week 3>\n";
        exit(-1);
    }
    my ($week_1, $week_2, $week_3) = @ARGV;
    
    my $input_file = "$currency/$input_filename";
    my @features = ();
    my %bits_dict = ();
    open IN, "<", $input_file or die "$input_file: $!";
    while (<IN>) {
        chomp;
        my @F = split /,/;
        if (abs($F[3]) > $score_threshold) {
            $F[0] =~ m{^([\+\-])(\d+)-(\d+):(\d+)-(\d+):(\w+)$} or die "Feature format error: $F[0]";
            my $is_sell = $1 eq "-" ? 1 : 0;
            my ($min_width, $max_width, $min_height, $max_height, $bits) = ($2, $3, $4, $5, $6);
            push @features, {
                "is_sell" => $is_sell,
                    "min_width" => $min_width,
                    "max_width" => $max_width,
                    "min_height" => $min_height,
                    "max_height" => $max_height,
                    "bits" => $bits,
                    "orig_str" => $F[0]
            };
            $bits_dict{$bits} = ();
        } 
        last if $F[1] > 1;
    }
    close IN;

    my @test_files;
    while (<$currency/weekly_past_data/week_*.csv>) {
        m{week_(\d{3})};
        next unless $1 >= $week_1 and $1 <= $week_3;
        push @test_files, $_;
    }

    my $output_file = "$currency/$output_filename";
    open OUT, ">", $output_file or die "$output_file: $!";
    OUT->autoflush();
    my @counts;
    my @sums;
    my @avrs;
    for my $test_file(@test_files) {
        print OUT "Test file: $test_file\n";
        $test_file =~ m{week_(\d{3})};
        my $test_num = $1;
        my $mode = ($test_num <= $week_2 ? 0 : 1);
        my @data;
        open IN, "<", $test_file or die "$test_file: $!";
        while (<IN>) {
            chomp;
            my @F = split /,/;
            push @data, [@F];
        }
        close IN;
        
        my $speed_over_time = 0;
        my $last_order_time = 0;
        for my $i(0..$#data) {
            if ($i >= $delay) {
                my $time = $data[$i-$delay]->[0];
                my $speed = $data[$i-$delay]->[6];
                $speed_over_time = $time if $speed > $speed_threshold;
                next if $time < $speed_over_time + $speed_wait;
                
                my $past_str = $data[$i-$delay]->[8];
                my @past_list = map { [split/:/] } split(m{/}, $past_str);
                for my $past(@past_list) {
                    my ($width, $height, $bits) = @{$past};
                    $width /= 10000;
                    next if not exists $bits_dict{$bits};
                    for my $feature(@features) {
                        if ($bits eq $feature->{"bits"} and
                            $width >= $feature->{"min_width"} and
                            $width <= $feature->{"max_width"} and 
                            $height >= $feature->{"min_height"} and
                            $height <= $feature->{"max_height"} and
                            $time > $feature->{"last_order_time"} + $order_wait) {
                            my $result_str = $data[$i]->[5];
                            my %result_dict = map { my @t = split/:/; ($t[0], [@t[1..$#t]]); } split(m{/}, $result_str);
                            die "time not exist: $result_time_key" if not exists $result_dict{$result_time_key};
                            my ($result_score, undef)  = @{$result_dict{$result_time_key}};
                            $result_score = -$result_score if $feature->{"is_sell"};
                            push @{$feature->{"results"}},
                            {
                                "file" => $test_file,
                                    "test_num" => $test_num,
                                    "time" => $time,
                                    "score" => $result_score
                            };
                            $feature->{"last_order_time"} = $time;
                        }
                    }
                }
            }
        }
    }
    close IN;
    for my $feature(@features) {
        print OUT qq{Feature: $feature->{"orig_str"}\n};
        for my $result(@{$feature->{"results"}}) {
            print OUT qq{$result->{"file"}:$result->{"time"} $result->{"score"}\n};
        }
    }
}

main();

# perl -Mutf8 -CSD -F/\\t/ -nale 'if (m{(2[1-5]0000:2[1-3]:387060607038)}) { $feature = $1;  m{60000:(\S+?):\d+,(\d+)}; $score = $1; $speed = $2; m{^(\d+)}; $time = $1; if ($time > $prev_time + 60000 or $time < $prev_time and $speed < 1000) { print "$ARGV $time $score"; $prev_time = $time; $score_all += $score; $count++; } } END { print "$count $score_all"; }' USDJPY/weekly_past_data/week_0[45]*
