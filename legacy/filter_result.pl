#!/usr/bin/env perl
use strict;
use warnings;
use utf8;
use open IO => ':utf8', ':std';

use Config::Simple;

my ($k_value, $threshold_value) = @ARGV;
my $cfg = new Config::Simple('config.ini');

while (my $line = <STDIN>) {
    chomp $line;
    my ($index, $coef1, $coef2, $knn_results, $profit_buy, $profit_sell) = split /,/, $line;
    my %knn_results = map { my ($k, @values) = split /\//; $k => \@values } split /:/, $knn_results;
    my $action = "pass";  # default action
    if ($knn_results{$k_value}->[0] >= $threshold_value) {
        $action = "buy";
    } elsif ($knn_results{$k_value}->[1] >= $threshold_value) {
        $action = "sell";
    }
    next if $action eq "pass";
    
    my $profit;
    if ($action eq "sell") {
        $profit = $profit_sell;
    } elsif ($action eq "buy") {
        $profit = $profit_buy;
    }
    print "$index アクション: $action 利益: $profit\n";
}
