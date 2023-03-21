#!/bin/sh
php download.php
./update.pl
./make_week_data.pl 40
./add_data.pl 50 120000
./add_past_data.pl 6 8 210000 220000 230000 240000 250000 260000 270000 280000 290000 300000
./test.pl 39 39
ulimit -n 10240
./stat.pl 0 35
./find_features.pl
./sort_features.pl
./check_features.pl 32 35 39
