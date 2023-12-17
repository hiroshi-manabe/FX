#!/usr/bin/env perl
use strict;
use warnings;
use utf8;
use open IO => ':utf8', ':std';
use Config::Simple;

my $cfg = new Config::Simple('config.ini');
my $currency = $cfg->param('settings.currency_pair');
my @window_times = @{$cfg->param('settings.window_times')};
my $commission = $cfg->param('settings.commission');
my $k_value = $cfg->param('settings.k_value');
my @r_squared_values = @{$cfg->param('settings.r_squared_values')};

my $last_week = $ARGV[0] // 59;      # Default value is 59 if not provided
my $test_week_num = $ARGV[1] // 20;  # Default value is 20 if not provided
my $test_begin_week = $last_week - $test_week_num;
my $initial_capital = 1000000;
my $cmd;

for my $r_squared_start_index(0..$#r_squared_values - 1) {
    my @r_temp = @r_squared_values[$r_squared_start_index..$#r_squared_values];
    $cfg->param("settings.test_r_squared_values", \@r_temp);
    $cfg->save();
    for my $min_profit(8..30) {
        $cfg->param("settings.min_profit", $min_profit);
        $cfg->save();
        $cmd = "./test_all.pl $last_week $test_week_num";
        print STDERR "$cmd\n";
        system $cmd;
        for (my $bet = 0.1; $bet < 3.5; $bet += 0.1) {
            my $sum = 0;
            my $capital = $initial_capital;
            for my $i($test_begin_week..$last_week-1) {
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
            if ($capital < $initial_capital) {
                print "Final capital ($capital) is less than initial capital ($initial_capital). Aborting.\n";
                last;
            }
        }
    }
}
