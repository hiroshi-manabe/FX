#!/usr/bin/env perl
use strict;
use utf8;
use open IO => ":utf8", ":std";

use Digest::MD5;
use File::Temp;

my $delay = 3;
my @times = qw(180000 210000 240000 270000 300000 330000 360000);
my %times_dict;
@times_dict{@times} = ();
my $scale_threshold = 4;
my $freq_threshold = 20;
my $in_dir = "weekly_past_data";
my $out_file_format = "stat_%d.csv";

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
#        next if $1 >= 1;
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
        for my $i(0..$#data) {
            if ($i >= $delay) {
               my $time = $data[$i-$delay]->[0];
                my $result_str = $data[$i]->[5];
                my %result_dict = map { my @t = split/:/; ($t[0], [@t[1..$#t]]); } split(m{/}, $result_str);
                my $past_str = $data[$i-$delay]->[6];
                my %past_dict = map { my @t = split/:/; ($t[0], [@t[1..$#t]]); } split(m{/}, $past_str);
                for my $key(keys %times_dict) {
                    die "$key not exist: $$key" if not exists $result_dict{$key};
                    my ($scale, $bits) = @{$past_dict{$key}};
                    my $past_key = join(":", $key, $bits);
                    if ($time < $wait_time_dict{$past_key}) {
                        next;
                    }
                    my ($result_score, $result_time)  = @{$result_dict{$key}};
                    my $hex = substr(Digest::MD5::md5_hex($bits), 0, 2);
                    next if $scale == 0 or $result_score == -1;
                    print { $fp_dict{$hex}->{"fp"} } join(",", join(":", $key, $scale, $bits), $result_score)."\n";
                    $wait_time_dict{$past_key} = $result_time;
                }
            }
        }
    }
    
    for my $i(0..255) {
        my $hex = sprintf("%02x", $i);
        close $fp_dict{$hex}->{"fp"};
    }
    
    my %fp_dict_out;
    for my $time(keys %times_dict) {
        my $out_file = sprintf("$currency/$out_file_format", $time);;
        $fp_dict{$time}->{"file"} = $out_file;
        open $fp_dict_out{$time}->{"fp"}, ">", $out_file or die qq{$out_file: $!};
    }
    
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
            push @{$dict{$time}->{$bits}}, [$scale, $result];
        }
        close $fp_dict{$hex}->{"fp"};
        for my $time(sort { $a <=> $b }  keys %dict) {
            for my $key(sort keys %{$dict{$time}}) {
                my $freq = scalar @{$dict{$time}->{$key}};
                next if $freq < $freq_threshold;
                my $prev_scale = 0;
                my $sum = 0;
                my $count = 0;
                for my $t((sort { $a->[0] <=> $b->[0]; } @{$dict{$time}->{$key}}), [0, 0]) {
                    my ($scale, $r) = @{$t};
                    if ($prev_scale and $scale != $prev_scale) {
                        my $avr = $sum / $count;
                        print { $fp_dict_out{$time}->{"fp"} } "$time:$prev_scale:$key,$count,$avr\n";
                        $sum = 0;
                        $count = 0;
                    }
                    $sum += $r;
                    $count++;
                    $prev_scale = $scale;
                }
            }
        }
    }
    for my $time(keys %times_dict) {
        close $fp_dict_out{$time}->{"fp"};
    }
}

main();
