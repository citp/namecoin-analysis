#!/usr/bin/env python3

import pdb
import pickle

import matplotlib.pyplot as plt
from matplotlib import rc, rcParams
from collections import Counter
import numpy as np

def num_possible_names(length):
    if length < 1:
        raise ValueError("Length must be positive, was given: " + str(length))
    if length == 1:
        return 26 # Starts with alphabet character
    if length == 2:
        return 26 * 36 #starts with alphabet, ends with alphanumeric
    else:
        return 26 * 36 * (37**(length - 2))
        

# rc('font', family='sans-serif') 
rc('font', serif='Helvetica Neue') 
rc('text', usetex='true') 
rcParams.update({'font.size': 16})
rcParams.update({'figure.autolayout': True})

# histogram = Counter()
# with open("plotNameLength.txt", "r") as histogram_file:
#     for line in histogram_file:
#         line = line.replace("\n", "")
#         length, count = line.split(" ")
#         length = int(length)
#         count = int(count)
#         histogram[length] = count
with open("name_lengths.pickle", "rb") as pickle_file:
    histogram = pickle.load(pickle_file)

# plt.hist(list(histogram.elements()), bins = len(histogram.items()))
histogram_elements = np.array(list(histogram[i] for i in range(1, 40)))
plt.hist(list(histogram.elements()), bins = range(0, 40),
         color = "#9ebcda")
# ax2 = plt.twinx()

# possible_names_count = np.array([num_possible_names(i) for i in
#                                   range(1, len(histogram_elements) + 1)])
# possible_names_available = (possible_names_count - histogram_elements) / possible_names_count
# possible_names_taken = (histogram_elements) / possible_names_count

# ax2.plot(range(1, len(histogram_elements) + 1), possible_names_taken)
# ax2.set_yscale('log')

plt.xlabel(r"\textbf{Name Length}")
plt.ylabel(r"\textbf{Frequency}")
plt.savefig("name_length_histogram.eps")
# plt.show()
