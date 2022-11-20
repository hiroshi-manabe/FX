#!/usr/bin/env perl
use strict;
use utf8;
use open IO => ":utf8", ":std";

use Digest::MD5;

my @currency_list = qw(USDJPY);
my $delay = 3;
my $time_width = 60000;
my $threshold = 10;
my $temp_dir = "./stat_temp";

sub main {
    mkdir $temp_dir if not -d $temp_dir;
    die "Cannot mkdir: $temp_dir" if not -d $temp_dir;
    for my $currency(@currency_list) {
        my %fp_dict;
        for my $i(0..255) {
            my $hex = sprintf("%02x", $i);
            $fp_dict{$hex}->{"file"} = "$temp_dir/$hex.csv";
            open $fp_dict{$hex}->{"fp"}, ">", $fp_dict{$hex}->{"file"} or die;
        }
        while (<$currency/weekly_past_data/week_*.csv>) {
            my %processed_dict = ();
            my $next_time = 0;
            
            m{week_(\d{3})};
            next if $1 < 65 or $1 >= 522;
            print "$_\n";
            
            m{/([^/]+)$};
            my $filename = $1;
            my @data = ();
            open IN, "<", $_ or die;
            while (<IN>) {
                chomp;
                my @F = split /,/;
                push @data, [@F];
            }
            close IN;
            for my $i(0..$#data) {
                if ($i >= $delay) {
                    my $time = $data[$i-$delay]->[0];
                    next if $time < $next_time;
                    my $past = $data[$i-$delay]->[6];
                    next if $past eq "";
                    my ($result, $result_time) = split/:/, $data[$i]->[5];
                    next if $result_time == -1;
                    if (exists $processed_dict{$past.$result_time}) {
                        next;
                    }
                    else {
                        my $hex = substr(Digest::MD5::md5_hex($past), 0, 2);
                        print { $fp_dict{$hex}->{"fp"} } join(",", $past, $result, $result_time - $time)."\n";
                        $processed_dict{$past.$result_time} = ();
                        $next_time = $result_time;
                    }
                }
            }
        }
        for my $i(0..255) {
            my $hex = sprintf("%02x", $i);
            close $fp_dict{$hex}->{"fp"};
        }
        
        open OUT, ">", "$currency/stat.csv";
        for my $i(0..255) {
            my $hex = sprintf("%02x", $i);
            open $fp_dict{$hex}->{"fp"}, "<", $fp_dict{$hex}->{"file"} or die;
            my %dict = ();
            while (readline($fp_dict{$hex}->{"fp"})) {
                chomp;
                my @F = split/,/;
                push @{$dict{$F[0]}}, [@F[1, 2]];
            }
            close $fp_dict{$hex}->{"fp"};
            for my $key(sort keys %dict) {
                my $count = scalar @{$dict{$key}};
                next if $count < $threshold;
                my $sum;
                $sum += $_->[0] for @{$dict{$key}};
                next if $sum < 0;
                print OUT join(",", $key, @{$_})."\n" for @{$dict{$key}};
            }
            unlink $fp_dict{$hex}->{"file"};
        }
        close OUT;
    }
    rmdir $temp_dir;
}

main();
