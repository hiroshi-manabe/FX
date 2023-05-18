#!/usr/bin/env perl
use strict;
use utf8;
use open IO => ":utf8", ":std";

use Config::Simple;
use IO::Handle;

sub main() {
    die "command <time_width> ..." if @ARGV < 1;
    my $arg_str = join(" ", @ARGV);

    my $cfg = new Config::Simple('config.ini');
    my $currency = $cfg->param('settings.currency_pair');
    
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
        my $cmd = qq{./add_past_data $arg_str < $_ > $file_to_write};
        print OUT "$cmd\n";
        system $cmd;
    }
    my $cmd = qq{parallel -v -j 8 :::: commands.txt};
    system($cmd);
}

main();
