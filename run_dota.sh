#!/bin/bash

# e.g. ./run_test.sh 3_2_10
# Result can be found in "./result/3_2_10.txt"

if [ ! -d result ]; then
mkdir result
fi

> ./result/$1.txt # clear file

# if [ $1 == 1 ] 
# then
#     echo 1
# fi

if [ $1 == OTAs ] 
then
    for filename in examples/DOTA/OTAs/*.json; do
        echo "$filename"
        python stats.py dota OTAs $filename
    done
else
    for i in $(seq 1 10) # iterate files
    do
    python stats.py dota $1 $1-$i.json
    done
fi
# Statistics
# python -c "import stats; stats.analyze(\""./result/$1.txt"\")" 

# 