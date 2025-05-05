#!/usr/bin/env perl
use strict;
use warnings;
use Config::Simple;

# Check for three arguments
die "Usage: $0 min_profit min_r_squared leverage\n" unless @ARGV == 3;

# Assign arguments to variables
my ($min_profit, $min_r_squared, $leverage) = @ARGV;

# Read configuration file
my $cfg = new Config::Simple('config.ini') or die Config::Simple->error();

# Update min_profit
$cfg->param('settings.min_profit', $min_profit);

# Process r_squared_values
my @r_squared_values = @{$cfg->param('settings.r_squared_values')};
my @filtered_r_squared_values = grep { $_ >= $min_r_squared } @r_squared_values;
$cfg->param('settings.test_r_squared_values', join(', ', @filtered_r_squared_values));

# Write changes to config.ini
$cfg->save() or die $cfg->error();

# Output leverage to file
my $currency_pair = $cfg->param('settings.currency_pair');
open my $fh, '>', "$currency_pair/leverage.csv" or die "Could not open file: $!";
print $fh $leverage . "\n";
close $fh;

my $cmd = "./test_all.pl";
system $cmd;
$cmd = "./convert_data.pl 59 20";
system $cmd;
$cmd = "cp -pf $currency_pair/results_59/params.csv $currency_pair/params.csv";
system $cmd;

$cmd = "cp -pf $currency_pair/{training_data,params,leverage}.csv '/Volumes/[C] Windows 11.hidden/Users/manabe/AppData/Roaming/MetaQuotes//Terminal/Common/Files'";
system $cmd;

print "Configuration and leverage output completed.\n";
