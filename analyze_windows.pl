#!/usr/bin/env perl
use strict;
use utf8;
use open IO => ":utf8", ":std";

use Time::Local qw(timegm);

sub main() {
    my $min_window_width = 200;
    my $bet = 60;
    
    my $first_year = 117;
    my $first_mon = 0;
    my $first_day = 6;
    my $last_year = 121;
    my $last_mon = 10;
    my $last_day = 6;
    my $time = timegm(0, 0, 0, $first_day, $first_mon, $first_year);
    my $last_time = timegm(0, 0, 0, $last_day, $last_mon, $last_year);
    while (1) {
        my (undef, undef, undef, $day, $mon, $year, undef, undef, undef) = gmtime($time);
        $year += 1900;
        my $fri_path;
        for my $hour(21, 20) {
            $fri_path = sprintf("USDJPY/%04d/%02d/%02d/%02dh_ticks.csv", $year, $mon, $day, $hour);
            last if -f $fri_path;
        }
        my $fri_date = sprintf("%04d/%02d/%02d", $year, $mon+1, $day);
        
        $time += 60 * 60 * 24 * 2;
        (undef, undef, undef, $day, $mon, $year, undef, undef, undef) = gmtime($time);
        $year += 1900;
        my $mon_path;
        for my $hour(21, 22) {
            $mon_path = sprintf("USDJPY/%04d/%02d/%02d/%02dh_ticks.csv", $year, $mon, $day, $hour);
            last if -f $mon_path;
        }
        my $mon_date = sprintf("%04d/%02d/%02d", $year, $mon+1, $day);

        $time += 60 * 60 * 24 * 5;
        last if $time > $last_time;

        if (not -f $fri_path) {
            print STDERR "Not exists: $fri_path\n";
            next;
        }
        if (not -f $mon_path) {
            print STDERR "Not exists: $mon_path\n";
            next;
        }
        
        open IN, "<", $fri_path or die;
        my @fri_tick_data = ();
        while (<IN>) {
            chomp;
            @fri_tick_data = split/,/;
        }
        close IN;

        open IN, "<", $mon_path or die;
        my @mon_tick_data = ();
        while (<IN>) {
            chomp;
            @mon_tick_data = split/,/;
            last;
        }
        close IN;
        # print "Friday last tick($fri_date): ".join(",", @fri_tick_data)."\n";
        # print "Monday first tick($mon_date): ".join(",", @mon_tick_data)."\n";
        printf("$mon_date Window: %d\n", $mon_tick_data[1] - $fri_tick_data[1]);
        if (abs($mon_tick_data[1] - $fri_tick_data[1]) >= $min_window_width) {
            print "Window detected.\n";
        }
        else {
            print "Window not detected.\n";
            next;
        }

        my $is_sell = $mon_tick_data[1] > $fri_tick_data[1];
        my @order_list = qw(Buy Sell);
        my $order_str = $order_list[$is_sell];
        my $column = 1 + $is_sell;
        my $another_column = 2 - $is_sell;
        my $price = 0;
        my $stop_loss = 0;
        my $take_profit = 0;
        my $sign = ($is_sell) ? -1 : 1;

        open IN, "<", $mon_path or die;
        while (<IN>) {
            chomp;
            my @tick_data = split/,/;
            if ($price == 0) {
                $price = $tick_data[$column];
                $take_profit = $price + $bet * $sign;
                $stop_loss = $tick_data[$another_column] - $bet * $sign;
                print "Order ($order_str) at $price, take profit: $take_profit, stop loss: $stop_loss\n";
            }
            elsif ($is_sell and $tick_data[$another_column] <= $take_profit or not $is_sell and $tick_data[$another_column] >= $take_profit) {
                print "Take profit at $take_profit (buy: $tick_data[1], sell: $tick_data[2])\n";
                last;
            }
            elsif ($is_sell and $tick_data[$another_column] >= $stop_loss or not $is_sell and $tick_data[$another_column] <= $stop_loss) {
                print "Stop loss at $stop_loss (buy: $tick_data[1], sell: $tick_data[2])\n";
                last;
            }
        }
    }
}

main();

