#!/usr/bin/env perl
use strict;
use utf8;
use open IO => ":utf8", ":std";

sub main() {
    my ($file, $bit_width, $time_width, $bit_height, $pips_height) = @ARGV;
    open IN, "<", $file or die;

    my $byte_count = ($bit_width * $bit_height - 1) / 8 + 1;
    my $time_factor = $time_width / $bit_width;
    my $price_factor = $pips_height / $bit_height;

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

    for (my $i = 0; $i < scalar(@orig_list); ++$i) {
#        print $orig_list[$i].",";
        my $cur_time = $time_list[$i];
        if ($cur_time >= $time_width - 1) {
            my $start_time = $cur_time - $time_width + 1;
            my $cur_price = $price_list[$i];
            my $min_price = $cur_price - $pips_height / 2;
            my $bits = "\x0" x $byte_count;
            for (my $j = $i; $time_list[$j] >= $start_time and $j >= 0; --$j) {
                my $time = $time_list[$j];
                my $price = $price_list[$j];
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
#            print $hex."\n";
        }
    }
}

main();
