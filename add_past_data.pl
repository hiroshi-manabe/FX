#!/usr/bin/env perl
use strict;
use utf8;
use open IO => ":utf8", ":std";
use IO::Handle;

use MIME::Base64;


sub main() {
    die "command <bit_width> <time_width> <bit_height> <overwrite>" if @ARGV != 4;
    my ($bit_width, $time_width, $bit_height, $overwrite) = @ARGV;
    my $currency;
    while (<currency_??????>) {
        m{currency_(.{6})};
        $currency = $1;
    }
    while (<$currency/weekly_data/week_*.csv>) {
        print "$_\n";
        my $file_to_write = $_;
        $file_to_write =~ s{/weekly_data/}{/weekly_past_data/};
        my $dir_to_write = $file_to_write;
        $dir_to_write =~ s{[^/]*$}{};
        mkdir $dir_to_write if not -d $dir_to_write;
        next if !$overwrite and -s $file_to_write;
        my $file_to_write_temp = $file_to_write;
        $file_to_write_temp .= ".tmp";
        my $cmd = qq{./add_past_data $bit_width $time_width $bit_height < $_ > $file_to_write_temp};
        print "$cmd\n";
        system $cmd;
        my $cmd = qq{mv $file_to_write_temp $file_to_write};
        system $cmd;
    }
}

main();
