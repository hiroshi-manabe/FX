#!/bin/sh
php download.php
./update.pl
./make_week_data.pl 40
./add_data.pl 50 120000
./add_past_data.pl 6 8 120000
./test.pl 39 39
ulimit -n 10240
./stat.pl 0 35
./find_features.pl
./sort_features.pl
./check_features.pl 32 35 39
