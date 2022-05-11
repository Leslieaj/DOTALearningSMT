#!/bin/bash

for filename in examples/MMT/OCMMs/*.json; do
    echo "$filename"
    python stats.py OCMMs $filename
done
# python -m unittest tests.ocmm_learner_test