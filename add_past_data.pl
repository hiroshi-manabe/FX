#!/usr/bin/env perl
use strict;
use utf8;
use open IO => ":utf8", ":std";
use IO::Handle;

use MIME::Base64;


sub main() {
    die "command <max_speed> <bit_width> <bit_height> <time_width> ..." if @ARGV < 5;
    my $arg_str = join(" ", @ARGV);
    my $currency;
    while (<currency_??????>) {
        m{currency_(.{6})};
        $currency = $1;
    }
    my $is_first = 1;
    while (<$currency/weekly_data/week_*.csv>) {
        print "$_\n";
        my $file_to_write = $_;
        $file_to_write =~ s{/weekly_data/}{/weekly_past_data/};
        my $dir_to_write = $file_to_write;
        $dir_to_write =~ s{[^/]*$}{};
        if ($is_first and -d $dir_to_write) {
            system("rm -fr $dir_to_write/*");
            $is_first = 0;
        }
        elsif (not -d $dir_to_write) {
            mkdir $dir_to_write;
        }
        my $file_to_write_temp = $file_to_write;
        $file_to_write_temp .= ".tmp";
        my $cmd = qq{./add_past_data $arg_str < $_ > $file_to_write_temp};
        print "$cmd\n";
        system $cmd;
        my $cmd = qq{mv $file_to_write_temp $file_to_write};
        system $cmd;
    }
}

main();
