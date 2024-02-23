#!/usr/bin/env perl
use strict;
use warnings;

use Config::Simple;

my $cfg = new Config::Simple('config.ini');
my $currency = $cfg->param('settings.currency_pair');
my $min_k_value = $cfg->param('settings.min_k_value');
my $max_k_value = $cfg->param('settings.max_k_value');
my @window_times = @{$cfg->param('settings.window_times')};
my @r_squared_values = @{$cfg->param('settings.r_squared_values')};

# Check if the command-line arguments are provided
if (@ARGV != 3) {
    print "Usage: perl script_name.pl <start_week> <end_week> <training_weeks>\n";
    exit;
}

my $commands_file = "commands.txt";

my $start_week = $ARGV[0];
my $end_week = $ARGV[1];
my $training_weeks = $ARGV[2];

my $root_directory = "./$currency";

if ($start_week < 0) {
    print "Error: Start week cannot be negative.\n";
    exit;
}

open(my $fh, '>', $commands_file) or die "Could not open file '$commands_file' $!";

my %lines_dict = ();
for my $week($start_week .. $end_week) {
    my $week_str = sprintf("%03d", $week);
    my @files = <$currency/weekly_digest/week_${week_str}_*.csv>;
    die "Multiple files: week $week" if @files > 1;
    open IN, "<", $files[0] or die "$!: $files[0]";
    while (<IN>) {
        chomp;
        my @F = split/,/;
        my $key = join("/", $week, $F[1], $F[2]);
        $lines_dict{$key}++;
    }
    close IN;
}

for (my $development_week = $start_week + $training_weeks; $development_week <= $end_week; $development_week++) {
    my $training_start_week = $development_week - $training_weeks;
    my $training_end_week = $development_week - 1;
    for my $window_time (@window_times) {
        my $output_dir = sprintf("%s/%02d/%05d", $root_directory, $development_week, $window_time);
        system("rm -fr $output_dir") if -d $output_dir;
        system("mkdir -p $output_dir") if not -d $output_dir;
        for my $r_squared_value (@r_squared_values) {
            my $output_file = sprintf("$output_dir/%.4f.txt", $r_squared_value);
            my $output_file_lines = sprintf("$output_dir/%.4f_lines.txt", $r_squared_value);
            my $cmd;
            $cmd = qq{./test.py $training_start_week $training_end_week $development_week $development_week --min_k_value $min_k_value --max_k_value $max_k_value --window_time $window_time --r_squared_value $r_squared_value > $output_file};
            print $fh "$cmd\n";
            my $count = 0;
            for my $week($training_start_week .. $training_end_week) {
                my $key = join("/", $week, $window_time, $r_squared_value);
                $count += exists $lines_dict{$key} ? $lines_dict{$key} : 0;
            }
            open OUT, ">", $output_file_lines or die "$!: $output_file_lines";
            print OUT "$count\n";
            close OUT;
        }
    }
}
close($fh);
my $cmd = qq{parallel -v -j 8 :::: commands.txt};
print "Running: $cmd\n";
system($cmd);

