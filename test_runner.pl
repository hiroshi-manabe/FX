#!/usr/bin/env perl
use strict;
use utf8;
use open IO => ':utf8', ':std';

use Config::Simple;

my $file = "result_all_bet_2.txt";

my $cfg = new Config::Simple('config.ini');
my $cmd;
unlink $file;

my @r_squared_values = @{$cfg->param('settings.r_squared_values')};
for my $r_squared_start_index(0..$#r_squared_values - 1) {
    my @r_temp = @r_squared_values[$r_squared_start_index..$#r_squared_values];
    $cfg->param("settings.test_r_squared_values", \@r_temp);
    $cfg->save();
    for my $min_profit(8..20) {
        $cfg->param("settings.min_profit", $min_profit);
        $cfg->save();
        $cmd = "./test_all.pl";
        print "$cmd\n";
        system $cmd;
        for (my $bet = 0.1; $bet < 3.5; $bet += 0.1) {
            $cfg->param("settings.bet", $bet);
            $cfg->save();
            $cmd = qq{./extract_matching.pl >> $file};
            print "$cmd\n";
            system $cmd;
        }
    }
}
