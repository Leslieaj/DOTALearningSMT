#!/bin/bash
> result/OCMMs.txt
for filename in examples/MMT/OCMMs/*.json; do
    echo "$filename"
    python stats.py ocmm OCMMs $filename
done
