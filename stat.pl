#!/usr/bin/env perl
use strict;
use utf8;
use open IO => ":utf8", ":std";

use Digest::MD5;

my @currency_list = qw(USDJPY);
my $delay = 3;
my $time_width = 60000;
my $scale_threshold = 4;
my $freq_threshold = 20;
my $temp_dir = "./stat_temp";

sub main {
    mkdir $temp_dir if not -d $temp_dir;
    die "Cannot mkdir: $temp_dir" if not -d $temp_dir;
    for my $currency(@currency_list) {
        my %fp_dict;
        for my $i(0..255) {
            my $hex = sprintf("%02x", $i);
            $fp_dict{$hex}->{"file"} = "$temp_dir/$hex.csv";
            open $fp_dict{$hex}->{"fp"}, ">", $fp_dict{$hex}->{"file"} or die $! ;
        }
        while (<$currency/weekly_past_data/week_*.csv>) {
            my %wait_time_dict = ();
            m{week_(\d{3})};
            next if $1 >= 346;
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
                    my $time = $data[$i-$delay-1]->[0];
                    my $past = $data[$i-$delay-1]->[6];
                    next if $past eq "";
                    my ($result, $result_time) = split/:/, $data[$i]->[5];
                    next if $result_time == -1;
                    if ($time < $wait_time_dict{$past}) {
                        next;
                    }
                    else {
                        my ($scale, $bits) = split/:/, $past;
                        my $hex = substr(Digest::MD5::md5_hex($bits), 0, 2);
                        print { $fp_dict{$hex}->{"fp"} } join(",", $past, $result.":".($result_time - $time))."\n";
                        $wait_time_dict{$past} = $result_time;
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
                my $past = $F[0];
                my $r = $F[1];
                my ($scale, $bits) = split/:/, $past;
                next if $scale < $scale_threshold;
                push @{$dict{$bits}}, [$scale, $F[1]];
            }
            close $fp_dict{$hex}->{"fp"};
            for my $key(sort keys %dict) {
                my $freq = scalar @{$dict{$key}};
                next if $freq < $freq_threshold;
                for my $t(sort { $a->[0] <=> $b->[0]; } @{$dict{$key}}) {
                    my ($scale, $r) = @{$t};
                    print OUT "$scale:$key,$r\n";
                }
            }
            unlink $fp_dict{$hex}->{"file"};
        }
        close OUT;
    }
    rmdir $temp_dir;
}

main();
