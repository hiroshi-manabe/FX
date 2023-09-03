#!/usr/bin/env perl
use strict;
use warnings;
use utf8;
use open IO => ':utf8', ':std';
use Config::Simple;

my $cfg = new Config::Simple('config.ini');
my $currency = $cfg->param('settings.currency_pair');
my @window_times = @{$cfg->param('settings.window_times')};
my @r_squared_values = @{$cfg->param('settings.test_r_squared_values')};
my $commission = $cfg->param('settings.commission');
my $min_profit = $cfg->param('settings.min_profit');
my $k_value = $cfg->param('settings.k_value');
my $bet = $cfg->param('settings.bet');

my $sum = 0;
my $capital = 1000000;

for my $i(39..58) {
    print "week $i\n";
    my $params_filename = sprintf("$currency/results_%02d/params.csv", $i);
    my %param_dict;
    open my $in_params, "<", $params_filename or die "$!: $params_filename";
    while (<$in_params>) {
        chomp;
        my @F = split /,/;
        $param_dict{$F[0]}->{$F[1]} = [@F[2, 3]];
    }
    close $in_params;

    my @matches = ();

    for my $window_time(@window_times) {
        next if not exists $param_dict{$window_time};
        my %dict;
        my $j = $i + 1;

        for my $r_squared(@r_squared_values) {
            next if not exists $param_dict{$window_time}->{$r_squared};
            my ($k, $threshold) = @{$param_dict{$window_time}->{$r_squared}};
            my $filename = sprintf("$currency/%02d/$window_time/$r_squared.txt", $j);
            open my $in, "<", $filename or die "$!: $filename";
            while (<$in>) {
                chomp;
                my @F = split /,/;
                my %t = map { my ($k, @v) = split m{/}; $k => \@v; } split/:/, $F[3];
                for my $is_sell(0, 1) {
                    my $sell_str = $is_sell ? "sell" : "buy";
                    my $v = $t{$k}->[$is_sell];
                    if ($v >= $threshold) {
                        my $pl = $F[4 + $is_sell] - $commission;
                        push @matches, [$F[0], $window_time, $r_squared, $is_sell, $pl];
                    }
                }
            }
            close $in;
        }
    }

    my $prev_time = -999999;
    for my $match(sort { $a->[0] <=> $b->[0]; } @matches) {
        my ($time, $window_time, $r_squared, $is_sell, $pl) = @{$match};
        next if $time < $prev_time + 300000;
        print join(", ", $time, $window_time, $r_squared, $is_sell ? "sell" : "buy", $pl)."\n";
        my $units = $capital * $bet;
        my $lot = int($units / 1000) / 100;
        my $units_adjusted = $lot * 100000;
        my $base = $capital / 130;
        my $rate = $units_adjusted / $base;
        my $result = $units_adjusted * ($pl / 1000);
        $capital += $result;
        print "Capital: $capital\n";
        $sum += $pl;
        $prev_time = $time;
    }
}

print "Sum: $sum\n";
print "Final capital: $capital k_value: $k_value min_profit: $min_profit bet: $bet r_squared: $r_squared_values[0]\n";
print qq{======================================================================\n};
