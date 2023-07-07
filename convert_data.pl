#!/usr/bin/env perl
use strict;
use warnings;
use utf8;
use open IO => ':utf8', ':std';
use Config::Simple;

my $cfg = new Config::Simple('config.ini');
my $currency = $cfg->param('settings.currency_pair');

my %params_dict = ();
die "convert_data.pl <last_week> <training_weeks>" if scalar(@ARGV) != 2;
my ($last_week, $training_weeks) = @ARGV;

my $params_file = sprintf("$currency/results_%02d/params.csv", $last_week);

open IN, "<", $params_file or die "$!: $params_file";
my $index = 0;
while (<IN>) {
    chomp;
    my @F = split/,/;
    $params_dict{join(",", @F[0, 1])} = $index;
    $index++;
}
close IN;


open OUT, ">", "$currency/training_data.csv";
for (my $week = $last_week - $training_weeks + 1; $week <= $last_week; ++$week) {
    my $week_str = sprintf("%03d", $week);
    my @files = <$currency/weekly_digest/week_${week_str}_*.csv>;
    die "Multiple files: week $week" if @files > 1;
    open IN, "<", $files[0] or die "$!: $files[0]";
    while (<IN>) {
        chomp;
        my @F = split/,/;
        my $key = join(",", @F[1, 2]);
        print OUT join(",", $params_dict{$key}, @F[3..6])."\n" if exists $params_dict{$key};
    }
    close IN;
}
