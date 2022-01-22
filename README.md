# NOTALearning
Learning nondeterministic one-clock timed automata


## Software Requirements
Running environment: Ubuntu 20.04 / Windows 
Python >= 3.8
- Install Z3-solver: `pip3 install z3-solver`
## Benchmarks

#### Deterministic one-clock timed automata
Stored in ./example/DOTA

#### Determinitsic one-clock mealy machine
Stored in ./example/MMT/OCMMs

## How to run tests

#### Deterministic one-clock timed automata
For deterministic one-clock automata benchmark, you can run with the `folder name` in ./example/DOTA
`./run_dota. folder name` e.g. `./run_dota.sh 3_2_10`
The experimental results are stored in ./result/`folder name`.txt
#### Determinitsic one-clock mealy machine
`./run_ocmm.sh`
The experimental results are stored in ./result/OCMMs.txt


