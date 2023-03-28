#!/bin/sh
php download.php
./update.pl
./make_week_data.pl 52
./add_data.pl 500 30000
./add_past_data.pl 6 8 120000
./make_past_data.pl 0 45
./test.py 46 48
