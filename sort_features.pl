#!/usr/bin/env perl
use strict;
use utf8;
use open IO => ":utf8", ":std";

sub main {
    my $input_filename = "stat2.csv";
    my $output_filename = "stat3.csv";
    
    my $currency;
    while (<currency_??????>) {
        m{currency_(.{6})};
        $currency = $1;
    }
    my $input_file = "$currency/$input_filename";

    my %count_dict;
    open IN, "<", $input_file or die "$input_file: $!";
    while (<IN>) {
        chomp;
        next unless s{^:}{};
        my @F = split /,/;
        $count_dict{$F[0]} = $F[1];
    }
    close IN;

    my %min_dict;
    my %dict;
    open IN, "<", $input_file or die "$input_file: $!";
    while (<IN>) {
        chomp;
        last if m{^:};
        my @F = split /,/;
        next unless $F[0] =~ m{^(.+?):(\w+)$};
        my $range = $1;
        my $bits = $2;
        my $t = $F[1] * $count_dict{$F[2]};
        if (not exists $min_dict{$bits} or $t < $min_dict{$bits}) {
            $min_dict{$bits} = $t;
            $dict{$bits} = [$range, @F[2, 3]];
        }
    }
    close IN;

    my $output_file = "$currency/$output_filename";
    open OUT, ">", $output_file or die "$output_file: $!";
    for my $bits(sort {$min_dict{$a}<=>$min_dict{$b}} keys %min_dict) {
        my $t = $min_dict{$bits};
        print OUT "$dict{$bits}->[0]:$bits,$t,$dict{$bits}->[1],$dict{$bits}->[2]\n";
    }
    close OUT;
}

main();
