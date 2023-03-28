#!/usr/bin/env perl
use strict;
use utf8;
use open IO => ":utf8", ":std";

use Config::Simple;

sub main() {
    die "command <width> <time> [time] ..." if @ARGV < 2 or @ARGV > 11;
    my $arg_str = join(" ", @ARGV);
    my $cfg = new Config::Simple('config.ini');
    my $currency = $cfg->param('settings.currency_pair');
    
    my $is_first = 1;
    while (<$currency/weekly/week_*.csv>) {
        print "$_\n";
        my $file_to_write = $_;
        $file_to_write =~ s{/weekly/}{/weekly_data/};
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
        my $cmd = qq{./add_data $arg_str < $_ > $file_to_write_temp};
        print $cmd."\n";
        system $cmd;
        my $cmd = qq{mv $file_to_write_temp $file_to_write};
        system $cmd;
    }
}

main();
