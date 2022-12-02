#!/usr/bin/env perl
use strict;
use utf8;
use open IO => ":utf8", ":std";

sub main() {
    my $currency;
    while (<currency_??????>) {
        m{currency_(.{6})};
        $currency = $1;
    }

    my $interval = 60000;
    my $count = 0;
    my $score = 0;
        
    while (<$currency/weekly_data/*.csv>) {
#    while (<temp_data_2.txt>) {
        my @windows = (
            { "step" => 1, "width" => 60000, "start_pos" => 0, "sum_x" => 0, "sum_y" => 0, "sum_x^2" => 0, "sum_y^2" => 0, "sum_xy" => 0, "b_1" => 0, "r^2" => 0, "min_b_1" => -99, "max_b_1" => -0.0007, "min_r^2" => 0.95, "is_ok" => 0 },
            { "step" => 10, "width" => 600000, "start_pos" => 0, "sum_x" => 0, "sum_y" => 0, "sum_x^2" => 0, "sum_y^2" => 0, "sum_xy" => 0, "b_1" => 0, "r^2" => 0, "mnin_b_1" => 0.003, "max_b_1" => 99, "min_r^2" => 0.8, "is_ok" => 0 },
            #        { "step" => 60, "width" => 3600000, "start_pos" => 0, "sum_x" => 0, "sum_y" => 0, "sum_x^2" => 0, "sum_y^2" => 0, "sum_xy" => 0, "b_1" => 0, "r^2" => 0,  "min_b_1" => 0.0001, "min_r^2" => 0.6, "is_ok" => 0 },
            );
        open IN, "<", $_ or die "$_: $!";
        print $_."\n";
        my @data_all = ();
        my $i = 0;
        my $prev_ok_time = -99999999;
        while (<IN>) {
            chomp;
            my ($time, $ask, $bid, undef, undef, $result) = split/,/;
            my ($result_score, $result_time) = split/:/, $result;
            push @data_all, [$time, $ask];
            for my $window(@windows) {
#                if ($i % $window->{"step"} == 01) {
                if (1) {
                    $window->{"sum_x"} += $time;
                    $window->{"sum_y"} += $ask;
                    $window->{"sum_x^2"} += $time ** 2;
                    $window->{"sum_y^2"} += $ask ** 2;
                    $window->{"sum_xy"} += $time * $ask;
                    while ($data_all[$window->{"start_pos"}]->[0] < $time - $window->{"width"}) {
                        my ($t, $a) = @{$data_all[$window->{"start_pos"}]};
                        $window->{"sum_x"} -= $t;
                        $window->{"sum_y"} -= $a;
                        $window->{"sum_x^2"} -= $t ** 2;
                        $window->{"sum_y^2"} -= $a ** 2;
                        $window->{"sum_xy"} -= $t * $a;
#                        $window->{"start_pos"} += $window->{"step"};
                        $window->{"start_pos"}++;
                    }
                    if ($time >= $window->{"width"}) {
                        my $n = $i - $window->{"start_pos"} + 1;
                        my $S_xx = $window->{"sum_x^2"} - ($window->{"sum_x"} ** 2) / $n;
                        my $S_xy = $window->{"sum_xy"} - ($window->{"sum_x"} * $window->{"sum_y"}) / $n;
                        my $b_1 = -9999;
                        $b_1 = $S_xy / $S_xx if $S_xx;
                        my $b_0 = ($window->{"sum_y"} - $b_1 * $window->{"sum_x"}) / $n;
                        my $SSE = $window->{"sum_y^2"} - $b_0 * $window->{"sum_y"} - $b_1 * $window->{"sum_xy"};
                        my $SST = $window->{"sum_y^2"} - ($window->{"sum_y"} ** 2) / $n;
                        if ($SST and $b_1 != -9999) {
                            my $r2 = 1 - $SSE / $SST;
#                            print "i: $i\twindow width:$window->{'width'}\tb_1:$b_1\tr^2:$r2\n";
                            $window->{"b_1"} = $b_1;
                            $window->{"r^2"} = $r2;
                            if ($b_1 < $window->{"max_b_1"} and $r2 > $window->{"min_r^2"}) {
                                $window->{"is_ok"} = 1;
                            }
                            else {
                                $window->{"is_ok"} = 0;
                            }
                        }
                        else {
                            $window->{"is_ok"} = 0;
                        }
                    }
                    else {
                        $window->{"is_ok"} = 0;
                    }
                }
            }
            my $flag_ok = 1;
            for my $window(@windows) {
                $flag_ok = 0 if $window->{"is_ok"} == 0;
            }
            if ($flag_ok == 1 and $time > $prev_ok_time + $interval) {
                $score += $result_score;
                $count++;
                my $avr = $score / $count;
                print "score: $score count: $count avr: $avr\n";
                $prev_ok_time = $time;
            }
            $i++;
        }
        close IN;
    }
}

main();

