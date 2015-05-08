#!/usr/bin/env python3

import pdb
import pickle

import matplotlib.pyplot as plt
from matplotlib import rc, rcParams
from collections import Counter
import numpy as np

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
with open("../segment_counts.pickle", "rb") as pickle_file:
    histogram = pickle.load(pickle_file)

# plt.hist(list(histogram.elements()), bins = len(histogram.items()))
plt.hist(histogram, bins = np.arange(9) - 0.5, color = "#9ebcda")
# ax2 = plt.twinx()

# possible_names_count = np.array([num_possible_names(i) for i in
#                                   range(1, len(histogram_elements) + 1)])
# possible_names_available = (possible_names_count - histogram_elements) / possible_names_count
# possible_names_taken = (histogram_elements) / possible_names_count

# ax2.plot(range(1, len(histogram_elements) + 1), possible_names_taken)
# ax2.set_yscale('log')

plt.xlabel(r"\textbf{Number of segments}")
plt.ylabel(r"\textbf{(Log) Number of names}")
plt.xticks(np.arange(8))
plt.yscale('log', nonposy='clip')
plt.savefig("segment_count_histogram.eps")
#plt.show()
