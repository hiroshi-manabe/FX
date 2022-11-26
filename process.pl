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
    die "$0 <min_count> <min_profit> [sell]" if @ARGV < 2 or @ARGV > 4;;
    my ($min_count, $min_profit, $flag) = @ARGV;
    my $sell_flag = 0;
    $sell_flag = 1 if $flag eq "sell";
    my $in_file = "$currency/$in_file_list[$sell_flag]";
    my $out_file = "$currency/$out_file_list[$sell_flag]";
    open IN, "<", $in_file or die "$in_file: $!";
    open OUT, ">", $out_file or die "$out_file: $!";
    my %output = ();
    my $sum;
    my $count;
    my %sum_dict;
    my %count_dict;
    my $prev_bits;
    while ($_ = (<IN> or "0:xxx,0:0")) {
        chomp;
        my ($scale, $bits, $result, undef) = split/[:,]/;
        if ($prev_bits ne "" and $bits ne $prev_bits) {
            my $count_all = sum(map { $count_dict{$_} } keys %count_dict);
            if ($count_all >= $min_count) {
                my $has_profit = 0;
                for my $s(keys %sum_dict) {
                    $has_profit = 1 if $sum_dict{$s} / $count_dict{$s} >= $min_profit;
                }
                if ($has_profit) {
                    my @scale_list = sort {$a<=>$b} keys %sum_dict;
                    my @best_params;
                    my $best_profit = 0;
                    for (my $i = 0; $i < scalar(@scale_list); ++$i) {
                        for (my $j = $i + 1; $j <= scalar(@scale_list); ++$j) {
                            my $profit = sum(@sum_dict{@scale_list[$i..$j-1]});
                            my $count = sum(@count_dict{@scale_list[$i..$j-1]});
                            next if ($profit / $count) < $min_profit;
                            if ($profit > $best_profit) {
                                $best_profit = $profit;
                                @best_params = ($i, $j-1);
                            }
                        }
                    }
                    
                    my $profit_all = sum(@{sum_dict}{@scale_list[$best_params[0]..$best_params[1]]});
                    my $count_all = sum(@{count_dict}{@scale_list[$best_params[0]..$best_params[1]]});
                    my $profit_avr = $profit_all / $count_all;
                    print OUT "$scale_list[$best_params[0]]-$scale_list[$best_params[1]]:$prev_bits,$count_all,$profit_avr\n" if $count_all >= $min_count;
                }
            }
            %sum_dict = ();
            %count_dict = ();
            $count_all = 0;
        }
        last if $bits eq "xxx";
        $sum_dict{$scale} += $result;
        $count_dict{$scale}++;
        $prev_bits = $bits;
    }
}

main();
