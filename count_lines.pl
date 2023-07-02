#!/usr/bin/env perl
use strict;
use warnings;

use Config::Simple;

my $cfg = new Config::Simple('config.ini');
my $currency = $cfg->param('settings.currency_pair');
my @window_times = @{$cfg->param('settings.window_times')};
my @r_squared_values = @{$cfg->param('settings.r_squared_values')};

my ($start_week, $end_week, $window_time, $r_squared_value) = @ARGV;

my $count = 0;
for my $week($start_week .. $end_week) {
    my $week_str = sprintf("%03d", $week);
    my @files = <$currency/weekly_digest/week_${week_str}_*.csv>;
    die "Multiple files: week $week" if @files > 1;
    open IN, "<", $files[0] or die "$!: $files[0]";
    while (<IN>) {
        chomp;
        my @F = split/,/;
        $count++ if $F[1] == $window_time and $F[2] == $r_squared_value;
    }
    close IN;
}
print "$count\n";
