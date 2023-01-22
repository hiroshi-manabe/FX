#!/bin/sh
php download.php
./update.pl
./make_week_data.pl 20
./add_data.pl 50 60000
./add_past_data.pl 6 8 210000 220000 230000 240000 250000 260000 270000 280000 290000 300000
./stat.pl 0 19
./find_features.pl
./sort_features.pl
