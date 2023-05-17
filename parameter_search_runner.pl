#!/usr/bin/env perl

use strict;
use warnings;

#for (my $i = 39; $i <= 50; ++$i) {
for (my $i = 50; $i <= 50; ++$i) {
    my $cmd;
    $cmd = qq{./parameter_search.pl $i 20 20};
    print "Running: $cmd\n";
    system($cmd);

    $cmd = qq{parallel -j 8 :::: commands.txt};
    print "Running: $cmd\n";
    system($cmd);
}
