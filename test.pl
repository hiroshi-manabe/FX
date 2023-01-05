#!/usr/bin/env perl
use strict;
use utf8;
use open IO => ":utf8", ":std";

use IO::Handle;
use List::Util qq(sum);

my $in_file = "features_final.csv";
my $delay = 3;

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
        my $is_sell = (s{^([\+\-])}{} and $1 eq "-") ? 1 : 0;
        my ($time_width, $min_scale, $max_scale, $bits) = split/[\-,:]/;
        $features{"$time_width:$bits"} = [$min_scale, $max_scale, $is_sell];
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
            my %past_dict = map { my @t = split/:/; ($t[0], [@t[1..$#t]]); } split(m{/}, $past_str);
            if ($order) {
                if (($order->{"is_sell"} eq "buy" and
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
                    my $key = $order->{"key"};
                    $score_by_feature{$key} += $profit;
                    $count_by_feature{$key}++;
                    print OUT qq{Order close: time $order->{"time"} time width $order->{"time_width"} $order->{"is_sell"} key $order->{"key"} profit $profit\n};
                    $order = undef;
                }
            }
            for my $time_width(sort { $a<=>$b } keys %past_dict) {
                my ($scale, $bits) = @{$past_dict{$time_width}};
                my $key = "$time_width:$bits";
                if (not $order and exists $features{$key}) {
                    my ($min_scale, $max_scale, $is_sell) = @{$features{$key}};
                    if ($scale >= $min_scale and $scale <= $max_scale) {
                        my $sign = $is_sell ? - 1 : 1;
                        my $str = $is_sell ? "sell" : "buy";

                        print OUT "Order: time $time time width $time_width $str key $key range $min_scale-$max_scale scale $scale\n";
                        $order = { "price" => $price, "time" => $time, "time_width" => $time_width, "is_sell" => $str, "key" => $key};
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
    for my $key(keys %features) {
        my $score = $score_by_feature{$key};
        my $count = $count_by_feature{$key};
        my $avr = 0;
        $avr = $score / $count if $count;
        my ($min_scale, $max_scale, $is_sell) = @{$features{$key}};
        my ($time_width, $bits) = split/:/, $key;
        my $sign = $is_sell ? "-" : "+";
        print OUT "$sign$time_width:$min_scale-$max_scale:$bits score $score count $count average $avr\n";
    }
    close OUT;
    `cp -pf $out_file $latest_file`;
}

main();
