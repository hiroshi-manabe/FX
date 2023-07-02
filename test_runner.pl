#!/usr/bin/env perl
use strict;
use utf8;
use open IO => ':utf8', ':std';

use Config::Simple;

my $file = "result_all_window_times.txt";

my $cfg = new Config::Simple('config.ini');
my $cmd;
unlink $file;

for my $freq_pow(0..7) {
    my $min_freq = 2 ** $freq_pow;
    my $max_freq = 2 ** ($freq_pow + 1) - 1;
    for (my $min_profit = 2; $min_profit <= 40; $min_profit += 2) {
        $cfg->param("settings.test_min_freq", $min_freq);
        $cfg->param("settings.test_max_freq", $max_freq);
        $cfg->param("settings.test_min_profit", $min_profit);
        $cfg->save();
        $cmd = "./test_all.pl";
        print "$cmd\n";
        system $cmd;
        $cmd = qq{echo "$min_freq,$max_freq,$min_profit" >> result_all.txt; ./simulate_bet.pl >> result_all.txt};
        print "$cmd\n";
        system $cmd;
    }
}

# window_times=10000, 10900, 11900, 13000, 14100, 15400, 16800, 18300, 20000, 21800, 23800, 26000, 28200, 30800, 33600, 36600, 40000, 43600, 47600, 52000, 56400, 61600, 67200, 73200, 80000, 87200, 95200, 104000, 112800, 123200, 134400, 146400, 160000, 174400, 190400, 208000, 225600, 246400, 268800, 292800, 320000, 348800, 380800, 416000, 451200, 492800, 537600, 585600, 640000

=pod
my @window_times_orig = (10000, 10900, 11900, 13000, 14100, 15400, 16800, 18300, 20000, 21800, 23800, 26000, 28200, 30800, 33600, 36600, 40000, 43600, 47600, 52000, 56400, 61600, 67200, 73200);

for my $skip_count(1..8) {
    my @window_times = @window_times_orig[grep { $_ % $skip_count == 0; } 0..$#window_times_orig];
    my @to_write = @window_times;
    $cfg->param("settings.window_times", \@to_write);
    my $str = join(", ", @to_write);
    $cfg->save();
    $cmd = "./test_all.pl";
    print "$cmd\n";
    system $cmd;
    $cmd = qq{echo "$str" >> $file; ./simulate_bet.pl >> $file};
    print "$cmd\n";
    system $cmd;
}
=cut
