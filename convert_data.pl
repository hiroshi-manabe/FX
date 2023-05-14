#!/usr/bin/env perl
use strict;
use warnings;
use utf8;
use open IO => ':utf8', ':std';
use Config::Simple;

my $cfg = new Config::Simple('config.ini');
my $currency = $cfg->param('settings.currency_pair');

my %params_dict = ();

open IN, "<", "$currency/params.csv" or die "$!: $currency/params.csv";
while (<IN>) {
    chomp;
    my @F = split/,/;
    $params_dict{$F[0]} = $F[1];
}
close IN;

my $last_week = 51;
my $training_weeks = shift @ARGV;

open OUT, ">", "$currency/training_data.csv";
for (my $week = $last_week - $training_weeks + 1; $week <= $last_week; ++$week) {
    my $week_str = sprintf("%03d", $week);
    my @files = <$currency/weekly_digest/week_${week_str}_*.csv>;
    die "Multiple files: week $week" if @files > 1;
    open IN, "<", $files[0] or die "$!: $files[0]";
    while (<IN>) {
        chomp;
        my @F = split/,/;
        print OUT join(",", $F[1], @F[3..6])."\n" if abs($F[2] - $params_dict{$F[1]}) < 0.000000001;
    }
    close IN;
}
