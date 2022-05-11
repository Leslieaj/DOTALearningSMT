#!/bin/bash

# e.g. ./run_test.sh 3_2_10
# Result can be found in "./result/3_2_10.txt"

if [ ! -d result ]; then
mkdir result
fi

> ./result/$1.txt # clear file

for i in $(seq 1 10) # iterate files
do
python stats.py $1 $1-$i.json
done

# Statistics
<<<<<<< HEAD
python -c "from stats import analyze; analyze(\""./result/$1.txt"\")" 
=======
python -c "import stats; stats.analyze(\""./result/$1.txt"\")" 
>>>>>>> f0c3ac3c00576e17e6620c26c5d033b924255a4e

