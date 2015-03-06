#!/usr/bin/env python3

import matplotlib.pyplot as plt
from matplotlib import rc, rcParams
from collections import Counter

# rc('font', family='sans-serif') 
rc('font', serif='Helvetica Neue') 
rc('text', usetex='true') 
rcParams.update({'font.size': 16})
rcParams.update({'figure.autolayout': True})

histogram = Counter()
with open("plotNameLength.txt", "r") as histogram_file:
    for line in histogram_file:
        line = line.replace("\n", "")
        length, count = line.split(" ")
        length = int(length)
        count = int(count)
        histogram[length] = count

# plt.hist(list(histogram.elements()), bins = len(histogram.items()))
plt.hist(list(histogram.elements()), bins = range(0, 40),
         color = "#9ebcda")
# plt.title("Frequency of Name Length", y = 1.02)
plt.xlabel(r"\textbf{Name Length}")
plt.ylabel(r"\textbf{Frequency}")
plt.savefig("name_length_histogram.eps")
# plt.show()
