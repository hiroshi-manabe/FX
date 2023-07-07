#!/usr/bin/env perl
use strict;
use utf8;
use open IO => ':utf8', ':std';

use Config::Simple;

my $file = "result_all_bet_2.txt";

my $cfg = new Config::Simple('config.ini');
my $cmd;
unlink $file;

for my $min_profit(12..20) {
    $cfg->param("settings.test_min_profit", $min_profit);
    $cfg->save();
    $cmd = "./test_all.pl";
    print "$cmd\n";
    system $cmd;
    for (my $bet = 0.1; $bet < 5.0; $bet += 0.1) {
        $cfg->param("settings.bet", $bet);
        $cfg->save();
        $cmd = qq{./extract_matching.pl >> $file};
        print "$cmd\n";
        system $cmd;
    }
}
