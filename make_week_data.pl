#!/usr/bin/env perl
use strict;
use utf8;
use open IO => ":utf8", ":std";

use Time::Local qw(timegm);

sub main() {
    my $min_window_width = 200;
    my $bet = 60;
    my $currency;
    while (<currency_??????>) {
        m{currency_(.{6})};
        $currency = $1;
    }
    die "$currency: Not found" if not -d $currency;
    mkdir "$currency/weekly" if not -d "$currency/weekly";
    my $first_year = 116;
    my $first_mon = 0;
    my $first_day = 4;
    my $time = timegm(0, 0, 0, $first_day, $first_mon, $first_year);
    my $week_index = 0;
    while (1) {
        my (undef, undef, undef, $day, $mon, $year, undef, undef, undef) = gmtime($time);
        $year += 1900;
        my $mon_path;

        my $found_flag = 0;
        my $cur_time = $time;
        my $time_offset = 0;
        
        while (1) {
            my (undef, undef, $cur_hour, $cur_day, $cur_mon, $cur_year, undef, undef, undef) = gmtime($cur_time);
            $cur_time += 3600;
            last if $cur_time - $time >= 60 * 60 * 24 * 7;
            my $cur_path = sprintf("$currency/%04d/%02d/%02d/%02dh_ticks.csv", $cur_year + 1900, $cur_mon, $cur_day, $cur_hour);
            if (not $found_flag and -s $cur_path) {
                print STDERR "Found: $cur_path\n";
                open OUT, ">", sprintf("$currency/weekly/week_%03d_%04d%02d%02d.csv", $week_index++, $cur_year + 1900, $cur_mon, $cur_day);
                $found_flag = 1;
            }
            if ($found_flag and not -s $cur_path) {
                print STDERR "Not found: $cur_path\n";
                close OUT;
                last;
            }
            if ($found_flag) {
                open IN, "<", $cur_path;
                while (<IN>) {
                    chomp;
                    my @F = split/,/;
                    $F[0] += $time_offset;
                    print OUT join(",", @F)."\n";
                }
                close IN;
                $time_offset += 3600 * 1000;
            }
        }
        last if not $found_flag;
        $time += 24 * 60 * 60 * 7;
    }
}

main();

