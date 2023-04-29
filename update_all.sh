#!/bin/sh
php download.php
./update.pl
./make_week_data.pl 52
./add_data.pl 15000 30000 45000 60000 75000
./add_past_data.pl 60000 120000 180000 240000 300000
./make_past_data.py 0 51 --r_squared_values 0.92 0.9225 0.925 0.9275 0.93 0.9325 0.935 0.9375 0.94 0.9425 0.945 0.9475 0.95 0.9525 0.955 0.9575 0.96 0.9625 0.965 0.9675 0.97
./parameter_search.pl 20 20
./test.py --stdin --num_processes 8 < commands.txt
./generate_csv.pl
./find_optimal.py | ./report_to_params.pl > USDJPY/params.csv 
