#!/usr/bin/env perl
use strict;
use utf8;
use open IO => ":utf8", ":std";

use IO::Handle;
use List::Util qq(sum);

my ($sec, $min, $hour, $mday, $mon, $year, undef, undef, undef) = localtime(time);

my @in_file_list = qw(stat_%d.csv stat_sell_%d.csv);
my @out_file_list = qw(features_%d.csv features_sell_%d.csv);

sub main {
    die "$0 <time> <min_scale> <max_scale> <min_count> <min_profit> [sell]" if @ARGV < 5 or @ARGV > 6;
    my $currency;
    while (<currency_??????>) {
        m{currency_(.{6})};
        $currency = $1;
    }
    my ($time, $min_scale, $max_scale, $min_count, $min_profit, $flag) = @ARGV;
    my $sell_flag = 0;
    $sell_flag = 1 if $flag eq "sell";
    my $in_file = sprintf("$currency/$in_file_list[$sell_flag]", $time);
    my $out_file = sprintf("$currency/$out_file_list[$sell_flag]", $time);
    open IN, "<", $in_file or die "$in_file: $!";
    open OUT, ">", $out_file or die "$out_file: $!";
    my %output = ();
    my $sum;
    my $count;
    my $prev_bits;
    my @list;
    while ($_ = (<IN> or "0:0:xxx,0:0")) {
        chomp;
        my ($time, $scale, $bits, $c, $avr, undef) = split/[:,]/;
        if ($prev_bits ne "" and $bits ne $prev_bits) {
            if ($count) {
                my $flag_ok = 0;
              LOOP:
                for (my $i = 0; $i < scalar(@list); ++$i) {
                    for (my $j = $i; $j < scalar(@list); ++$j) {
                        my $count_all = List::Util::sum(map { $_->[0] } @list[$i..$j]);
                        my $score_all = List::Util::sum(map { $_->[0] * $_->[1] } @list[$i..$j]);
                        my $avr_all = $score_all / $count_all;
                        if ($count_all >= $min_count and ((not $sell_flag and $avr_all >= $min_profit) or ($sell_flag and $avr_all <= -$min_profit))) {
                            $flag_ok = 1;
                            last;
                        }
                    }
                }
                if ($flag_ok) {
                    print "$_\n" for map { $_->[2]; } @list;
                }
            }
            $sum = 0;
            $count = 0;
            @list = ();
        }
        last if $bits eq "xxx";
        if ($scale >= $min_scale and $scale <= $max_scale) {
            push @list, [$c, $avr, $_];
        }
        $prev_bits = $bits;
    }
    close OUT;
}

main();
