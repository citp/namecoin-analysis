#!/usr/bin/env python3

import matplotlib.pyplot as plt
from collections import Counter

histogram = Counter()
with open("plotNameLength.txt", "r") as histogram_file:
    for line in histogram_file:
        line = line.replace("\n", "")
        length, count = line.split(" ")
        length = int(length)
        count = int(count)
        histogram[length] = count

# plt.hist(list(histogram.elements()), bins = len(histogram.items()))
plt.hist(list(histogram.elements()), bins = range(0, 40))
plt.title("Frequency of Name Length")
plt.xlabel("Name Length")
plt.ylabel("Frequency")
plt.savefig("name_length_histogram.eps")
# plt.show()
