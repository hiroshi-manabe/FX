#!/usr/bin/env perl
use strict;
use utf8;
use open IO => ":utf8", ":std";

use Digest::MD5;
use File::Temp;

my $delay = 3;
my $time_width = 60000;
my $scale_threshold = 4;
my $freq_threshold = 20;
my @in_dir_list = qw(weekly_past_data weekly_past_sell_data);
my @out_dir_list = qw(stat.csv stat_sell.csv);

sub main {
    my $currency;
    while (<currency_??????>) {
        m{currency_(.{6})};
        $currency = $1;
    }
    my $sell_flag = 0;
    if (@ARGV) {
        my $temp = shift @ARGV;
        $sell_flag = 1 if $temp eq "sell";
    }
    my $temp_dir = File::Temp->newdir();
    my %fp_dict;
    for my $i(0..255) {
        my $hex = sprintf("%02x", $i);
        $fp_dict{$hex}->{"file"} = "$temp_dir/$hex.csv";
        open $fp_dict{$hex}->{"fp"}, ">", $fp_dict{$hex}->{"file"} or die qq{$fp_dict{$hex}->{"file"}: $!} ;
    }
    while (<$currency/$in_dir_list[$sell_flag]/week_*.csv>) {
        my %wait_time_dict = ();
        m{week_(\d{3})};
        next if $1 >= 344;
        print "$_\n";
        m{/([^/]+)$};
        my $filename = $1;
        my @data = ();
        open IN, "<", $_ or die "$_: $!";
        while (<IN>) {
            chomp;
            my @F = split /,/;
            push @data, [@F];
        }
        close IN;
        for my $i(0..$#data) {
            
            if ($i >= $delay) {
                my $time = $data[$i-$delay-1]->[0];
                my $result_str = $data[$i]->[5];
                my $c;
                $c = 0;
                my @results = map { [$c++, split/:/]; } split m{/}, $result_str;
                
                my $past_str = $data[$i-$delay-1]->[6];
                $c = 0;
                my @pasts = map { [$c++, split/:/] } split m{/}, $result_str;
                next if $past eq "";
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
    
    open OUT, ">", "$currency/$out_dir_list[$sell_flag]" or die qq{"$currency/$out_dir_list[$sell_flag]: $!};
    for my $i(0..255) {
        my $hex = sprintf("%02x", $i);
        open $fp_dict{$hex}->{"fp"}, "<", $fp_dict{$hex}->{"file"} or die qq{$fp_dict{$hex}->{"file"}: $!};
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

main();
