#!/usr/bin/env perl
use strict;
use utf8;
use open IO => ":utf8", ":std";

use Statistics::Distributions;

my $stat_filename = "stat.csv";
my @probs = (0.18, 0.64, 0.18);

sub main {
    my $currency;
    while (<currency_??????>) {
        m{currency_(.{6})};
        $currency = $1;
    }
    my $stat_file = "$currency/$stat_filename";
    open IN, "<", $stat_file or die "$stat_file: $!";
    my %data = ();
    while (<IN>) {
        chomp;
        my @F = split/[:,]/;
        my $t = $F[4] >= 15 ? 2 : $F[4] <= -15 ? 0 : 1;
        $data{$F[0]}->{$F[3]}->[$F[1]]->[$F[2]]->[$t]++;
        $data{$F[0]}->{$F[3]}->[$F[1]]->[$F[2]]->[3] += $F[4];
        $data{$F[0]}->{$F[3]}->[$F[1]]->[$F[2]]->[4]++;
    }
    close IN;

    my %count_dict = ();
    for my $speed(0..2) {
        my $ref = $data{$speed};
        for my $width(1..5) {
            for my $height(1..5) {
                for my $bits(keys %{$ref}) {
                    for my $x(21..31-$width) {
                        for my $y(10..31-$height) {
                            my $score_sum = 0;
                            my $count_sum = 0;
                            my @sums = ();
                            for my $w(0..$width-1) {
                                for my $h(0..$height-1) {
                                    for my $i(0..2) {
                                        $sums[$i] += $ref->{$bits}->[$x+$w]->[$y+$h]->[$i];
                                    }
                                    $score_sum += $ref->{$bits}->[$x+$w]->[$y+$h]->[3];
                                    $count_sum += $ref->{$bits}->[$x+$w]->[$y+$h]->[4];
                                }
                            }
                            next if not $count_sum;
                            my $avr = $score_sum / $count_sum;
                            my $xx = $x + $width - 1;
                            my $yy = $y + $height - 1;
                            my $all;
                            for my $i(0..2) {
                                $all += $sums[$i];
                            }
                            next if $all < 10;
                            $count_dict{$all}++;
                            
                            my $is_sell = $sums[0] > $sums[2];
                            my $index = $is_sell ? 0 : 2;
                            my $another_index = $is_sell ? 2 : 0;
                            my $this = $sums[$index];
                            my $sign = $is_sell ? "-" : "+";
                            my $e = $all * $probs[$index];
                            my $v = $all * $probs[$index] * (1 - $probs[$index]);
                            my $z = abs(($this - $e) / sqrt($v));
                            my $uprob = Statistics::Distributions::uprob($z);
                            print "$sign$x-$xx:$y-$yy:$bits,$uprob,$count_sum,$avr\n";
                        }
                    }
                }
            }
        }
    }
    my $sum = 0;
    for my $count(sort {$b<=>$a} keys %count_dict) {
        print ":$count,$count_dict{$count}\n";
    }
}

main();
