#!/usr/bin/env perl
use strict;
use utf8;
use open IO => ":utf8", ":std";

while (<STDIN>) {
    chomp;
    next if m{^#};
    m{^(([\+\-])(\d+)-(\d+):(\d+)-(\d+):(\w+))$} or die;
    my $sign = $2 eq "+" ? 0 : 1;
    print qq{  {$sign, $3, $4, $5, $6, "$7", "$1"},\n};
}
