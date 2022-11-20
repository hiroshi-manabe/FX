#!/usr/bin/env perl
use strict;
use utf8;
use open IO => ":utf8", ":std";

my @currency_list = qw(USDJPY);
sub main() {
    die "command <width> <time> <overwrite>" if @ARGV != 3;
    my ($width, $time, $overwrite) = @ARGV;
    for my $currency(@currency_list) {
        while (<$currency/weekly/week_*.csv>) {
            print "$_\n";
            my $file_to_write = $_;
            $file_to_write =~ s{/weekly/}{/weekly_sell_data/};
            my $dir_to_write = $file_to_write;
            $dir_to_write =~ s{[^/]*$}{};
            mkdir $dir_to_write if not -d $dir_to_write;
            next if !$overwrite and -s $file_to_write;
            my $file_to_write_temp = $file_to_write;
            $file_to_write_temp .= ".tmp";
            my $cmd = qq{./add_sell_data $width $time < $_ > $file_to_write_temp};
            print $cmd."\n";
            system $cmd;
            my $cmd = qq{mv $file_to_write_temp $file_to_write};
            system $cmd;
        }
    }
}

main();

