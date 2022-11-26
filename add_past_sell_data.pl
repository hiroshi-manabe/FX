#!/usr/bin/env perl
use strict;
use utf8;
use open IO => ":utf8", ":std";
use IO::Handle;

use MIME::Base64;

my @currency_list = qw(USDJPY);

sub main() {
    die "command <bit_width> <time_width> <bit_height> <overwrite>" if @ARGV != 4;
    my ($bit_width, $time_width, $bit_height, $overwrite) = @ARGV;
    for my $currency(@currency_list) {
        while (<$currency/weekly_sell_data/week_*.csv>) {
            print "$_\n";
            my $file_to_write = $_;
            $file_to_write =~ s{/weekly_sell_data/}{/weekly_past_sell_data/};
            my $dir_to_write = $file_to_write;
            $dir_to_write =~ s{[^/]*$}{};
            next if !$overwrite and -s $file_to_write;
            mkdir $dir_to_write if not -d $dir_to_write;
            my $file_to_write_temp = $file_to_write;
            $file_to_write_temp .= ".tmp";
            my $cmd = qq{./add_past_data $bit_width $time_width $bit_height < $_ > $file_to_write_temp};
            print "$cmd\n";
            system $cmd;
            my $cmd = qq{mv $file_to_write_temp $file_to_write};
            system $cmd;
        }
    }
}

main();
