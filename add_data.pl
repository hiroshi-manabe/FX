#!/usr/bin/env perl
use strict;
use utf8;
use open IO => ":utf8", ":std";

sub main() {
    die "command <width> <time> ..." if @ARGV < 3 or @ARGV % 2 == 0;
    my $arg_str = join(" ", @ARGV);
    my $currency;
    while (<currency_??????>) {
        m{currency_(.{6})};
        $currency = $1;
    }
    while (<$currency/weekly/week_*.csv>) {
        print "$_\n";
        my $file_to_write = $_;
        $file_to_write =~ s{/weekly/}{/weekly_data/};
        my $dir_to_write = $file_to_write;
        $dir_to_write =~ s{[^/]*$}{};
        mkdir $dir_to_write if not -d $dir_to_write;
        my $file_to_write_temp = $file_to_write;
        $file_to_write_temp .= ".tmp";
        my $cmd = qq{./add_data $arg_str < $_ > $file_to_write_temp};
        print $cmd."\n";
        system $cmd;
        my $cmd = qq{mv $file_to_write_temp $file_to_write};
        system $cmd;
    }
}

main();

