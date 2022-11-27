#!/usr/bin/env perl
use strict;
use utf8;
use open IO => ":utf8", ":std";

use IO::Handle;
use List::Util qq(sum);

my ($sec, $min, $hour, $mday, $mon, $year, undef, undef, undef) = localtime(time);

my $currency = "USDJPY";
my @in_file_list = qw(stat.csv stat_sell.csv);
my @out_file_list = qw(features.csv features_sell.csv);

sub main {
    die "$0 <min_scale> <max_scale> <min_count> <min_profit> [sell]" if @ARGV < 4 or @ARGV > 5;
    my ($min_scale, $max_scale, $min_count, $min_profit, $flag) = @ARGV;
    my $sell_flag = 0;
    $sell_flag = 1 if $flag eq "sell";
    my $in_file = "$currency/$in_file_list[$sell_flag]";
    my $out_file = "$currency/$out_file_list[$sell_flag]";
    open IN, "<", $in_file or die "$in_file: $!";
    open OUT, ">", $out_file or die "$out_file: $!";
    my %output = ();
    my $sum;
    my $count;
    my $prev_bits;
    while ($_ = (<IN> or "0:xxx,0:0")) {
        chomp;
        my ($scale, $bits, $result, undef) = split/[:,]/;
        if ($prev_bits ne "" and $bits ne $prev_bits) {
            if ($count) {
                my $avr = $sum / $count;
                if ($count >= $min_count and $avr > $min_profit) {
                    print OUT "$min_scale-$max_scale:$prev_bits,$count,$avr\n";
                }
            }
            $sum = 0;
            $count = 0;
        }
        last if $bits eq "xxx";
        if ($scale >= $min_scale and $scale <= $max_scale) {
            $sum += $result;
            $count++;
        }
        $prev_bits = $bits;
    }
    close OUT;
}

main();
