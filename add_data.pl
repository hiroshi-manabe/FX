#!/usr/bin/env perl
use strict;
use utf8;
use open IO => ":utf8", ":std";

use Config::Simple;

sub main() {
    die "command <loss-cut>" if @ARGV != 1;
    my $cfg = new Config::Simple('config.ini');
    my $currency = $cfg->param('settings.currency_pair');
    my @window_times = @{$cfg->param('settings.window_times')};
    my $arg_str = join(" ", @ARGV, map { $_ / 4; } @window_times);
    
    my $is_first = 1;
    open OUT, ">", "commands.txt";
    while (<$currency/weekly/week_*.csv>) {
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
        my $cmd = qq{./add_data $arg_str < $_ > $file_to_write};
        print OUT $cmd."\n";
    }
    my $cmd = qq{parallel -v -j 8 :::: commands.txt};
    system($cmd);
}

main();
