#!/usr/bin/env perl
use strict;
use utf8;
use open IO => ":utf8", ":std";

use Config::Simple;

sub main() {
    my $cfg = new Config::Simple('config.ini');
    my $currency = $cfg->param('settings.currency_pair');
    my @r_squared_values = @{$cfg->param('settings.r_squared_values')};
    
    my $is_first = 1;
    open OUT, ">", "commands.txt";
    while (<$currency/weekly_past_data/week_*.csv>) {
        my $file_to_write = $_;
        $file_to_write =~ s{/weekly_past_data/}{/weekly_digest/};
        my $dir_to_write = $file_to_write;
        $dir_to_write =~ s{[^/]*$}{};
        if ($is_first and -d $dir_to_write) {
            system("rm -fr $dir_to_write/*");
            $is_first = 0;
        }
        elsif (not -d $dir_to_write) {
            mkdir $dir_to_write;
        }
        my $arg_str = join(" ", @r_squared_values);
        my $cmd = qq{./filter_digest $arg_str < $_ > $file_to_write};
        print OUT $cmd."\n";
    }
    my $cmd = qq{parallel -v -j 8 :::: commands.txt};
    system($cmd);
}

main();
