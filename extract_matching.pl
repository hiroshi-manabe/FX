#!/usr/bin/env perl
use strict;
use warnings;
use utf8;
use open IO => ':utf8', ':std';
use Config::Simple;

my $cfg = new Config::Simple('config.ini');
my $currency = $cfg->param('settings.currency_pair');
my @window_times = @{$cfg->param('settings.window_times')};
my @r_squared_values = @{$cfg->param('settings.r_squared_values')};
my $commission = $cfg->param('settings.commission');

for my $i(39..58) {
    for my $window_time(@window_times) {
        my %dict;
        my $j = $i + 1;
        my $stat_filename = sprintf("$currency/results_%02d/$window_time.csv", $i);
        open my $in_stat, "<", $stat_filename or die "$!: $stat_filename";
        while (<$in_stat>) {
            chomp;
            my @F = split /,/;
            my ($r_squared, $k, $threshold) = split m{/}, $F[0];
            next unless $k == 10;
            next unless $F[2] > 0;
            $dict{$r_squared}->{$k}->{$threshold} = [$F[1], $F[2]];
        }
        close $in_stat;

        for my $r_squared(@r_squared_values) {
            my $filename = sprintf("$currency/%02d/$window_time/$r_squared.txt", $j);
            open my $in, "<", $filename or die "$!: $filename";
            while (<$in>) {
                chomp;
                my @F = split /,/;
                my %t = map { my ($k, @v) = split m{/}; $k => \@v; } split/:/, $F[3];
                for my $is_sell(0, 1) {
                    my $sell_str = $is_sell ? "sell" : "buy";
                    for my $k(keys %t) {
                        next if not exists $dict{$r_squared}->{$k};
                        my $v = $t{$k}->[$is_sell];
                        my $ref = $dict{$r_squared}->{$k};
                        for my $threshold(sort {$a <=> $b;} keys %{$ref}) {
                            if ($v >= $threshold) {
                                my $pl = $F[4 + $is_sell] - $commission;
                                my ($freq, $avr_pl) = @{$ref->{$threshold}};
                                print join("\t", $j, $window_time, $r_squared, $F[0], $freq, $avr_pl, $pl)."\n" if $freq > 1;
                            }
                        }
                    }
                }
            }
            close $in;
        }
    }
}
