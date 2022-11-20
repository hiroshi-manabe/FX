#!/usr/bin/env perl
use strict;
use utf8;
use open IO => ":utf8", ":std";

use IO::Handle;

sub main {
    my ($bit_width, $bit_height) = @ARGV;
    while (<STDIN>) {
        print;
        chomp;
        my $bytes = pack("H*", $_);
        for (my $y = 0; $y < $bit_height; ++$y) {
            for (my $x = 0; $x < $bit_width; ++$x) {
                my $bit_pos = $y + $x * $bit_height;
                my $byte_index = $bit_pos >> 3;
                my $bit_data = 1 << ($bit_pos % 8);
                my $bit_is_set = (ord(substr($bytes, $byte_index, 1)) & $bit_data) ? 1 : 0;
                print $bit_is_set ? "■" : "□";
            }
            print "\n";
        }
        print "\n";
    }
}

main();
