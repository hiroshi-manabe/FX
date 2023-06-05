#!/usr/bin/env perl
use strict;
use utf8;
use open IO => ":utf8", ":std";

use Config::Simple;

my $cfg = new Config::Simple('config.ini');
my $currency = $cfg->param('settings.currency_pair');
my @window_times = @{$cfg->param('settings.window_times')};

my %dict = ();
for my $week(39..50) {
    my %dict_bet = ();
    open IN, "<", "$currency/results_$week/params.csv";
    while (<IN>) {
        chomp;
        my @F = split/,/;
        $dict_bet{$F[0]} = $F[4];
    }
    for my $window_time(keys %dict_bet) {
        open IN, "<", "$currency/results_$week/${window_time}_result.txt";
        my $time = 0;
        my $pl = 0;
        my $bet = $dict_bet{$window_time};
        while (<IN>) {
            chomp;
            if (m{\b利益: (\S+)}) {
                $time = $1;
                $pl = $2;
                $dict{$week}->{$time} = [$window_time, $bet, $pl];
            }
            
        }
    }
    close IN;
}
my $capital = 1000000;
for my $w(sort { $a <=> $b } keys %dict) {
    print qq{Week: $w\n};
    my $prev_t = 0;
    for my $t(sort { $a <=> $b } keys %{$dict{$w}}) {
        my ($window_time, $bet, $pl) = @{$dict{$w}->{$t}};
        if ($t < $prev_t + 300000) {
            print qq{Pass: $w $t $window_time\n};
        }
        else {
            #            my $units = $capital * 1000 * $bet;
            my $units = $capital * 3.8;
            my $lot = int($units / 1000) / 100;
            my $units_adjusted = $lot * 100000;
            my $base = $capital / 130;
            my $rate = $units_adjusted / $base;
            my $result = $units_adjusted * ($pl / 1000);
            print qq{$w $t $window_time bet: $lot rate: $rate result: $result\n};
            $capital += $result;
            print qq{Capital: $capital\n};
        }
        $prev_t = $t;
    }
}
