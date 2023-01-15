#!/usr/bin/env perl
use strict;
use utf8;
use open IO => ":utf8", ":std";

use IO::Handle;
use List::Util qq(sum);

my $in_file = "features_final.csv";
my $delay = 3;
my $check_interval = 30000;
my $min_profit = 5;
my $test_width = 4;

sub main {
    my $currency;
    while (<currency_??????>) {
        m{currency_(.{6})};
        $currency = $1;
    }
    if (scalar(@ARGV) != 2) {
        print STDERR "$0 <start week> <end week>\n";
        exit(-1);
    }
    my ($start_week, $end_week) = @ARGV;
    my ($buy_take_profit, $buy_loss_cut, $sell_take_profit, $sell_loss_cut) = (1000, 50, 1000, 50);
    my $in_file = "$currency/$in_file";
    my ($sec, $min, $hour, $mday, $mon, $year, undef, undef, undef) = localtime(time);
    my $out_file = sprintf("$currency/test_result_%04d%02d%02d_%02d%02d%02d.txt", $year + 1900, $mon + 1, $mday, $hour, $min, $sec);
    print STDOUT "Output file: $out_file\n";
    my $latest_file = sprintf("$currency/test_result_latest.txt");
    
    open IN, "<", $in_file or die "$in_file: $!";
    my %features = ();
    while (<IN>) {
        chomp;
        next if m{^#};
        my $orig = $_;
        my $is_sell = (s{^([\+\-])}{} and $1 eq "-") ? 1 : 0;
        my ($min_width, $max_width, $min_height, $max_height, $bits) = split/[\-,:]/;
        $features{$bits} = [$min_width, $max_width, $min_height, $max_height, $is_sell, $orig];
    }
    close IN;

    my @test_files;
    while (<$currency/weekly_past_data/week_*.csv>) {
        m{week_(\d{3})};
        next unless $1 >= $start_week and $1 <= $end_week;
        push @test_files, $_;
    }

    open OUT, ">", $out_file or die;
    OUT->autoflush;
    my $hit_count_all = 0;
    my $score_all = 0;
    my %score_by_feature = ();
    my %count_by_feature = ();
    if (scalar(keys %features) == 0) {
        print OUT join(",", 0, 0, 0)."\n";
        next;
    }
    for my $test_file(@test_files) {
        print OUT "File: $test_file\n";
        my $score = 0;
        my $hit_count = 0;
        open IN, "<", $test_file or die "Cannot open: $test_file";
        my @data = ();
        my $order = undef;
        while (<IN>) {
            chomp;
            my @F = split/,/;
            my $price = $F[1];
            push @data, [@F];
            next if scalar(@data) <= $delay;
            my $time = $F[0];
            my $past_str = $data[-$delay-1]->[6];
            my %past_dict = map { my @t = split/:/; ($t[0], [$t[1], join(":", @t[2..$#t])]); } split(m{/}, $past_str);
            if ($order) {
                my $close_flag = 0;
                if ($time > $order->{"time"} + $order->{"prev_checked"} + $check_interval) {
                    if (($order->{"is_sell"} eq "buy" and
                         $price <= $order->{"prev_price"} + $min_profit) or
                        ($order->{"is_sell"} eq "sell" and
                         $price >= $order->{"prev_price"} - $min_profit)) {
                        $close_flag = 1;
                    }
                    else {
                        $order->{"prev_checked"} += $check_interval;
                        $order->{"prev_price"} = $price;
                    }
                }
                if (
                    $close_flag or
                    ($order->{"is_sell"} eq "buy" and
                     ($price >= $order->{"price"} + $buy_take_profit or
                      $price <= $order->{"price"} - $buy_loss_cut)) or
                    ($order->{"is_sell"} eq "sell" and
                     ($price <= $order->{"price"} - $sell_take_profit or
                      $price >= $order->{"price"} + $sell_loss_cut)) or
                     
                    $time > $order->{"time"} + $order->{"time_width"}) {
                    my $close_price = $price;
                    if ($order->{"is_sell"} eq "buy") {
                        $close_price = $order->{"price"} + $buy_take_profit if $price >= $order->{"price"} + $buy_take_profit;
                        $close_price = $order->{"price"} - $buy_loss_cut if $price <= $order->{"price"} - $buy_loss_cut;
                    }
                    elsif ($order->{"is_sell"} eq "sell") {
                        $close_price = $order->{"price"} - $sell_take_profit if $price <= $order->{"price"} - $sell_take_profit;
                        $close_price = $order->{"price"} + $sell_loss_cut if $price >= $order->{"price"} + $sell_loss_cut;
                    }
                    my $profit = ($close_price - $order->{"price"}) * ($order->{"is_sell"} eq "sell" ? -1 : 1);
                    
                    $score += $profit;
                    $hit_count++;
                    my $bits = $order->{"bits"};
                    $score_by_feature{$bits} += $profit;
                    $count_by_feature{$bits}++;
                    print OUT qq{Order close: time $order->{"time"} time width $order->{"time_width"} $order->{"is_sell"} key $order->{"key"} profit $profit\n};
                    $order = undef;
                }
            }
            for my $time_width(sort { $a<=>$b } keys %past_dict) {
                my $width = int($time_width / 10000);
                my ($height, $bits) = @{$past_dict{$time_width}};
                if (not $order and exists $features{$bits}) {
                    my ($min_width, $max_width, $min_height, $max_height, $is_sell, $key) = @{$features{$bits}};
                    my $sign = $is_sell ? - 1 : 1;
                    my $str = $is_sell ? "sell" : "buy";
                    if ($width >= $min_width and $width <= $max_width and $height >= $min_height and $height <= $max_height) {
                        print OUT "Order: time $time time width $time_width $str key $key width $width height $height\n";
                        $order = { "price" => $price, "time" => $time, "time_width" => $time_width, "is_sell" => $str, "key" => $key, "bits" => $bits, "prev_checked" => 0, "prev_price" => $price};
                    }
                }
            }
        }
        my $avr = 0;
        $avr = $score / $hit_count if $hit_count;
        print OUT "File total: score $score hit count $hit_count average score $avr\n";
        $hit_count_all += $hit_count;
        $score_all += $score;
        print OUT (("-" x 70)."\n");
    }
    my $avr_all = 0;
    $avr_all = $score_all / $hit_count_all if $hit_count_all;
    print OUT "Total: score $score_all hit count $hit_count_all average score $avr_all\n";
    for my $bits(keys %features) {
        my $score = $score_by_feature{$bits};
        my $count = $count_by_feature{$bits};
        my $avr = 0;
        $avr = $score / $count if $count;
        print OUT "$features{$bits}->[5] score $score count $count average $avr\n";
    }
    close OUT;
    `cp -pf $out_file $latest_file`;
}

main();
