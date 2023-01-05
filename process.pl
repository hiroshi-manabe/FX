#!/usr/bin/env perl
use strict;
use utf8;
use open IO => ":utf8", ":std";

use IO::Handle;
use List::Util qq(sum);

my ($sec, $min, $hour, $mday, $mon, $year, undef, undef, undef) = localtime(time);

my $in_file_format = qw(stat_%d.csv);
my @out_file_list = qw(features_%d.csv features_sell_%d.csv);

sub main {
    die "$0 <time> <max_scale_width> <min_count> <min_profit> [sell]" if @ARGV < 4 or @ARGV > 5;
    my $currency;
    while (<currency_??????>) {
        m{currency_(.{6})};
        $currency = $1;
    }
    my ($time, $max_scale_width, $min_count, $min_profit, $flag) = @ARGV;
    my $sell_flag = 0;
    $sell_flag = 1 if $flag eq "sell";
    my $in_file = sprintf("$currency/$in_file_format", $time);
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
            if (@list) {
                my ($max_i, $max_j) = (0, 0);
                my $max = 0;
              LOOP:
                for (my $i = 0; $i < scalar(@list); ++$i) {
                    next if $list[$i]->[2] > 25; # magic number!
                    for (my $j = $i; $j < scalar(@list); ++$j) {
                        next if $j - $i + 1 > $max_scale_width;
                        next if $list[$j]->[2] > 50;
                        
                        my $count_all = List::Util::sum(map { $_->[0] } @list[$i..$j]);
                        my $score_all = (List::Util::sum(map { $_->[0] * $_->[1] } @list[$i..$j])) * ($sell_flag ? -1 : 1);
                        next if $count_all == 0;
                        my $avr_all = $score_all / $count_all;
                        if ($score_all > $max and $count_all >= $min_count and $avr_all >= $min_profit) {
                            ($max_i, $max_j) = ($i, $j);
                            $max = $score_all;
                        }
                    }
                }
                if ($max) {
                    for (my $i = 0; $i < scalar(@list); ++$i) {
                        my $mark = "#" if $i >= $max_i and $i <= $max_j;
                        print OUT "$mark$list[$i]->[4]\n";
                        
                        if ($i == $max_j) {
                            my $template = $list[$i]->[3];
                            $template =~ s{xxx}{$list[$max_i]->[2]-$list[$max_j]->[2]};
                            print OUT "$template\n";
                        }
                    }
                }
            }
            @list = ();
        }
        last if $bits eq "xxx";
        my $template = join(":", ($sell_flag ? "-" : "+").$time, "xxx", $bits);
        push @list, [$c, $avr, $scale, $template, $_];
        $prev_bits = $bits;
    }
    close OUT;
}

main();
