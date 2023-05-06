#!/usr/bin/env perl

use strict;
use warnings;

for (my $i = 39; $i <= 50; ++$i) {
    print "Running: ./parameter_search.pl $i 20 20\n";
    system("./parameter_search.pl $i 20 20");

    print "Running: ./test.py --stdin --num_processes 8 < commands.txt\n";
    system("./test.py --stdin --num_processes 8 < commands.txt");
}
