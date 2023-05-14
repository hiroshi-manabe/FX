#!/bin/bash
perl parameter_search.pl
./test.py --stdin --num_processes 8 < commands.txt
