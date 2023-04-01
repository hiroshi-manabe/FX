#!/bin/sh
php download.php
./update.pl
./make_week_data.pl 1
./add_data.pl 15000 30000 45000 60000 75000
./add_past_data.pl 60000 120000 180000 240000 300000
#./make_past_data.pl 0 45
#python3 ./test.py 46 48
