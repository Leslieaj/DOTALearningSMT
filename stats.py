"""Collect and analysis experimental data."""

import sys,time
from ota import buildOTA
<<<<<<< HEAD
from smart_learner import learn_ota
from statistics import mean

=======
from ocmm import buildOCMM
from smart_learner import learn_ota
from statistics import mean

from ocmm_smart_learner import learn_ocmm

>>>>>>> f0c3ac3c00576e17e6620c26c5d033b924255a4e
def smt_learn_dota(folder_name, file_name):
    """Test the folder/file.json and write statistics into ./results/folder.txt"""
    with open("./result/%s.txt" % folder_name, "a") as output_file:
        locs = 0
        mems, eqs, timer = [], [], []
        trans_num = 0
        print("file name: %s", file_name)
        o = buildOTA("./examples/%s/%s" % (folder_name, file_name))
        trans_num += len(o.trans)
        start_time = time.perf_counter()
        learned_ota, mem_num, eq_num = learn_ota(o, limit=150, verbose=False)
        end_time = time.perf_counter()
        mems.append(mem_num)
        eqs.append(eq_num)
        loc = len(learned_ota.locations) - 1
        locs += loc
        output_file.write("Test %s: %s, Membership query: %d, Equivalence query: %d, Locations: %d, Transitions: %d \n" 
                    % (file_name, end_time - start_time, mem_num, eq_num, loc, trans_num))
        output_file.flush()

<<<<<<< HEAD
=======
def smt_learn_ocmm(folder_name, file_name):
    """Test the folder/file.json and write statistics into ./results/folder.txt"""
    with open("./result/%s.txt" % folder_name, "a") as output_file:
        locs = 0
        mems, eqs, timer = [], [], []
        trans_num = 0
        print("file name: %s", file_name)
        o = buildOCMM("./%s" % file_name)
        trans_num += len(o.trans)
        start_time = time.perf_counter()
        learned_ota, mem_num, eq_num = learn_ocmm(o, limit=150, verbose=False)
        end_time = time.perf_counter()
        mems.append(mem_num)
        eqs.append(eq_num)
        loc = len(learned_ota.locations) - 1
        locs += loc
        output_file.write("Test %s: %s, Membership query: %d (%d), Equivalence query: %d, Locations: %d, Transitions: %d Inputs: %d\n" 
                    % (file_name, end_time - start_time, mem_num, o.mq_num, eq_num, loc, trans_num, o.comp_input()))
        output_file.flush()

>>>>>>> f0c3ac3c00576e17e6620c26c5d033b924255a4e
def parse_data(file_name):
    """Parse the data in ./result/file_name.txt"""
    lines = open(file_name, "r").read().splitlines()
    test_data = []
    for line in lines:
        test_data.append([float(b.split(":")[1]) for b in line.split(",")])
    # time_data, mem_data, eq_data, locs, trans = list(zip(*test_data))
    return list(zip(*test_data))

def analyze(file_name):
    """Write the experimental result to ./result/file_name.txt. """
    time_data, mem_data, eq_data, locs, trans = parse_data(file_name)
    
    with open(file_name, "a") as f:
<<<<<<< HEAD
        f.write("Delta: %.3f #M_min: %d #M_mean: %.1f #M_max:%d #E_min:%d #E_mean:%.1f #E_max:%d l:%d t(s):%.3f" % (
=======
        f.write("Delta: %.3f #M_min: %d #M_mean: %.2f #M_max:%d #E_min:%d #E_mean:%.2f #E_max:%d l:%.1f t(s):%.3f" % (
>>>>>>> f0c3ac3c00576e17e6620c26c5d033b924255a4e
            mean(trans), min(mem_data), mean(mem_data), max(mem_data), min(eq_data), mean(eq_data), max(eq_data), mean(locs), mean(time_data)
        ))


if __name__ == "__main__":
    assert len(sys.argv) == 3, "Wrong arguments %s" % sys.argv
    folder_name, file_name = str(sys.argv[1]), str(sys.argv[2])
<<<<<<< HEAD
    smt_learn_dota(folder_name, file_name)
=======
    # smt_learn_dota(folder_name, file_name)
    smt_learn_ocmm(folder_name, file_name)
>>>>>>> f0c3ac3c00576e17e6620c26c5d033b924255a4e
