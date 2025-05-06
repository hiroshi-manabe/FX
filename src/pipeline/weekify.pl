#!/usr/bin/env perl
use strict;
use utf8;
use open IO => ":utf8", ":std";

use Config::Simple;
use Time::Local qw(timegm);

use lib "$FindBin::Bin/../../lib";  # adjust two dirs up from src/pipeline/
use FX::Paths qw(weekly_path);

sub main() {
    die "command <week num>" if @ARGV != 1;
    my $week_num = shift @ARGV;
    
    my $cfg = new Config::Simple('config.ini');
    my $currency = $cfg->param('settings.currency_pair');
    die "$currency: Not found" if not -d $currency;
    
    my $weekly_path = weekly_path();
    system("rm $weekly_path/*");

    my $cur_time = time;
    my (undef, undef, undef, $cur_day, $cur_mon, $cur_year, $cur_wday, undef, undef) = gmtime(time);
    my $cur_sunday_time = int($cur_time / (60 * 60 * 24)) * 60 * 60 * 24 - ($cur_wday + ($cur_wday == 6 ? 0 : 7))  * 60 * 60 * 24;
    my $week_start_time = $cur_sunday_time - (($week_num - 1) * 60 * 60 * 24 * 7);
    
    my $week_index = 0;
    while (1) {
        my $found_flag = 0;
        my $time = $week_start_time;
        my $time_offset = 0;
        
        while (1) {
            my (undef, undef, $hour, $day, $mon, $year, undef, undef, undef) = gmtime($time);
            $time += 3600;
            last if $time - $week_start_time >= 60 * 60 * 24 * 7;
            my $path = sprintf("$currency/%04d/%02d/%02d/%02dh_ticks.csv", $year + 1900, $mon, $day, $hour);
            if (not $found_flag and -s $path) {
                print STDERR "Found: $path\n";
                my $output_file = sprintf("$currency/weekly/week_%03d_%04d%02d%02d.csv", $week_index++, $year + 1900, $mon + 1, $day);
                open OUT, ">", $output_file or die "$output_file: $!";
                $found_flag = 1;
            }
            if ($found_flag and not -s $path) {
                print STDERR "Not found: $path\n";
                close OUT;
                last;
            }
            if ($found_flag) {
                open IN, "<", $path;
                while (<IN>) {
                    chomp;
                    my @F = split/,/;
                    $F[0] += $time_offset;
                    print OUT join(",", @F)."\n";
                }
                close IN;
                $time_offset += 3600 * 1000;
            }
        }
        last if not $found_flag;
        if ($week_start_time == $cur_sunday_time) {
            last;
        }
        $week_start_time += 24 * 60 * 60 * 7;
    }
}

main();

