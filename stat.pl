#!/usr/bin/env perl
use strict;
use utf8;
use open IO => ":utf8", ":std";

use Digest::MD5;
use File::Temp;

my $delay = 3;
my $scale_threshold = 4;
my $freq_threshold = 100;
my $in_dir = "weekly_past_data";
my $out_filename = "stat.csv";
my $result_time_key = 60000;
my $speed_threshold = 1000;
my $speed_wait = 600000;
my $diff_threshold = 200;
my $diff_wait = 600000;

sub main {
    my $currency;
    while (<currency_??????>) {
        m{currency_(.{6})};
        $currency = $1;
    }
    my $sell_flag = 0;
    if (@ARGV < 2 or @ARGV > 3) {
        print STDERR "$0 <start week> <end week> [sell]\n";
        exit(-1);
    }
    my $start_week = shift @ARGV;
    my $end_week = shift @ARGV;
    if (@ARGV) {
        $sell_flag = 1 if $ARGV[0] eq "sell";
    }
    my $temp_dir = File::Temp->newdir();
    my %fp_dict;
    for my $i(0..255) {
        my $hex = sprintf("%02x", $i);
        $fp_dict{$hex}->{"file"} = "$temp_dir/$hex.csv";
        open $fp_dict{$hex}->{"fp"}, ">", $fp_dict{$hex}->{"file"} or die qq{$fp_dict{$hex}->{"file"}: $!} ;
    }
    while (<$currency/$in_dir/week_*.csv>) {
        my %wait_time_dict = ();
        m{week_(\d{3})};
        next if $1 < $start_week or $1 > $end_week;
        my $week_diff = $end_week - $1;
        print "$_\n";
        m{/([^/]+)$};
        my $filename = $1;
        my @data = ();
        open IN, "<", $_ or die "$_: $!";
        while (<IN>) {
            chomp;
            my @F = split /,/;
            push @data, [@F];
        }
        close IN;
        my $speed_over_time = 0;
        my $diff_over_time = 0;
        for my $i(0..$#data) {
            if ($i >= $delay) {
                my $time = $data[$i-$delay]->[0];
                my $result_str = $data[$i]->[5];
                my %result_dict = map { my @t = split/:/; ($t[0], [@t[1..$#t]]); } split(m{/}, $result_str);
                my $speed = $data[$i-$delay]->[6];
                $speed_over_time = $time if $speed > $speed_threshold;
                my $diff = $data[$i-$delay]->[7];
                $diff_over_time = $time if $diff > $diff_threshold;
                next if $time < $speed_over_time + $speed_wait or $time < $diff_over_time + $diff_wait;
                
                my $past_str = $data[$i-$delay]->[8];
                my @past_list = map { [split/:/] } split(m{/}, $past_str);
                for my $past(@past_list) {
                    die "time not exist: $result_time_key" if not exists $result_dict{$result_time_key};
                    my ($time_width, $scale, $bits) = @{$past};
                    my $past_key = $bits;
                    if ($time < $wait_time_dict{$past_key}) {
                        next;
                    }
                    my ($result_score, $result_time)  = @{$result_dict{$result_time_key}};
                    my $hex = substr(Digest::MD5::md5_hex($bits), 0, 2);
                    next if $scale == 0 or $result_score == -1;
                    print { $fp_dict{$hex}->{"fp"} } join(",", join(":", int($time_width / 10000), $scale, $bits), $result_score)."\n";
                    $wait_time_dict{$past_key} = $result_time;
                }
            }
        }
    }
    
    for my $i(0..255) {
        my $hex = sprintf("%02x", $i);
        close $fp_dict{$hex}->{"fp"};
    }

    my $out_file = "$currency/$out_filename";
    open OUT, ">", $out_file or die qq{$out_file: $!};
    
    for my $i(0..255) {
        my $hex = sprintf("%02x", $i);
        open $fp_dict{$hex}->{"fp"}, "<", $fp_dict{$hex}->{"file"} or die qq{$fp_dict{$hex}->{"file"}: $!};
        my %dict = ();
        while (readline($fp_dict{$hex}->{"fp"})) {
            chomp;
            my @F = split/,/;
            my $past = $F[0];
            my $result = $F[1];
            my ($time, $scale, $bits) = split/:/, $past;
            next if $scale < $scale_threshold;
            push @{$dict{$bits}}, [$time, $scale, $result];
        }
        close $fp_dict{$hex}->{"fp"};
        for my $bits(sort keys %dict) {
            my $freq = scalar @{$dict{$bits}};
            next if $freq < $freq_threshold;
            for my $t(sort { $a->[1] <=> $b->[1] || $a->[0] <=> $b->[0] } @{$dict{$bits}}) {
                print OUT join(",", join(":", @{$t}[0..1], $bits), $t->[2])."\n";
            }
        }
    }
    close OUT;
}

main();
