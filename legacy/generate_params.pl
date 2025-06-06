#!/usr/bin/env perl
use strict;
use utf8;
use open IO => ':utf8', ':std';

use Config::Simple;

my $cfg = new Config::Simple('config.ini');
my $currency = $cfg->param('settings.currency_pair');
my @window_times = @{$cfg->param('settings.window_times')};

my $last_week = $ARGV[0] // 59;      # Default value is 59 if not provided
my $test_week_num = $ARGV[1] // 20;  # Default value is 20 if not provided
my $test_begin_week = $test_week_num * 2 - 1;

my $min_avr = $ARGV[2] // 0;
my $min_samples = $ARGV[3] // 0;

for my $i($test_begin_week..$last_week) {
    my $params_path = sprintf(qq{$currency/results_%02d/params.csv}, $i);
    open my $out, ">", $params_path or die "$!: $params_path";
    for my $window_time(@window_times) {
        my $dist_filename = sprintf("${currency}/results_%02d/${window_time}_dist.txt", $i);
        open my $dist_file, "<", $dist_filename or die "Cannot open $dist_filename: $!";
        my @dist_list;
        while (<$dist_file>) {
            chomp;
            push @dist_list, $_;
        }
        close $dist_file;
        my $csv_filename = sprintf("${currency}/results_%02d/${window_time}.csv", $i);
        open my $csv_file, "<", $csv_filename or die "Cannot open $csv_filename: $!";
        my %exists_dict = ();
        while (<$csv_file>) {
            chomp;
            my ($label, $samples, $avr, undef) = split/,/;
            next if $avr < $min_avr or $samples < $min_samples;
            $label =~ tr{/}{,};
            my $r_squared = (split/,/, $label)[0];
            if (not exists $exists_dict{$r_squared}) {
                print $out join(",", $window_time, $label, $samples, $avr)."\n";
                $exists_dict{$r_squared} = ();
            }
        }
        close $csv_file;
    }
    close $out;
}
