#!/usr/bin/env perl
use strict;
use utf8;
use open IO => ":utf8", ":std";

use Config::Simple;
use IO::Handle;

sub main() {
    my $cfg = new Config::Simple('config.ini');
    my $currency = $cfg->param('settings.currency_pair');
    my @window_times = @{$cfg->param('settings.window_times')};
    my $arg_str = join(" ", @window_times);
    
    my $is_first = 1;
    open OUT, ">", "commands.txt";
    while (<$currency/weekly_data/week_*.csv>) {
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
        my $cmd = qq{./fit_quadratic $arg_str < $_ > $file_to_write};
        print OUT "$cmd\n";
        system $cmd;
    }
    my $cmd = qq{parallel -v -j 8 :::: commands.txt};
    system($cmd);
}

main();
