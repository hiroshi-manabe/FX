#!/usr/bin/env perl
use strict;
use utf8;
use open IO => ":utf8", ":std";

sub main() {
    my ($file, $bit_width, $time_width, $bit_height) = @ARGV;
    open IN, "<", $file or die;

    my $byte_count = ($bit_width * $bit_height - 1) / 8 + 1;
    my $time_factor = $time_width / $bit_width;

    my @orig_list;
    my @time_list;
    my @price_list;
    while (<IN>) {
        chomp;
        push @orig_list, $_;
        my @F = split/,/;
        push @time_list, $F[0];
        push @price_list, $F[1];
    }
    close IN;

    my $movement_width = 300000;
    my $movement = 0;
    my $movement_start_index = 0;

    my $price_to_normalize = 100000;
    
    for (my $i = 0; $i < scalar(@orig_list); ++$i) {
        my $rate = $price_list[$i] / $price_to_normalize;
        my $movement_normalized = int($movement / $rate);
        my $str_to_print = $orig_list[$i].",$movement_normalized,";
        my $cur_time = $time_list[$i];
        $movement += abs($price_list[$i] - $price_list[$i-1]) if $i > 0;
        while ($time_list[$i] - $movement_width > $time_list[$movement_start_index]) {
            $movement_start_index++;
            $movement -= abs($price_list[$movement_start_index] - $price_list[$movement_start_index-1]);
        }
        if ($cur_time >= $time_width - 1) {
            my $start_time = $cur_time - $time_width + 1;
            my $min_rel_price = 0;
            my $max_rel_price = 0;
            my $bits = "\x0" x $byte_count;
            for (my $j = $i; $time_list[$j] >= $start_time and $j >= 0; --$j) {
                my $rel_price = int($price_list[$j] / $rate) - $price_to_normalize;
                if ($rel_price < $min_rel_price) {
                    $min_rel_price = $rel_price;
                }
                elsif ($rel_price > $max_rel_price) {
                    $max_rel_price = $rel_price;
                }
            }
            my $max_rel_price_bits = $bit_height / 2 - 1;
            my $min_rel_price_bits = -($bit_height / 2);
            my $price_factor_min = int((-$min_rel_price + -$min_rel_price_bits - 1) / -$min_rel_price_bits);
            my $price_factor_max = int(($max_rel_price + $max_rel_price_bits - 1) / $max_rel_price_bits);
            my $price_factor = 1;
            if ($price_factor_min > $price_factor) {
                $price_factor = $price_factor_min;
            }
            if ($price_factor_max > $price_factor) {
                $price_factor = $price_factor_max;
            }
            my $min_price = $price_to_normalize + ($min_rel_price_bits * $price_factor);
            for (my $j = $i; $time_list[$j] >= $start_time and $j >= 0; --$j) {
                my $time = $time_list[$j];
                my $price = int($price_list[$j] / $rate);
                my $time_diff = $time - $start_time;
                my $price_diff = $price - $min_price;
                my $time_index = int($time_diff / $time_factor);
                my $price_index = int($price_diff / $price_factor);
                my $bit_pos = $price_index + $time_index * $bit_height;
                my $byte_index = $bit_pos >> 3;
                my $bit_data = 1 << ($bit_pos % 8);
                if ($price_diff >= 0 and $price_index < $bit_height) {
                    substr($bits, $byte_index, 1, chr(ord(substr($bits, $byte_index, 1)) | $bit_data));
                }
            }
            my $hex = unpack("H*", $bits);
            $str_to_print .= "$price_factor:$hex";
#            print $hex."\n";
        }
        print "$str_to_print\n";
    }
}

main();
