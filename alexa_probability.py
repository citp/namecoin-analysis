#!/usr/bin/env python3

from sys import intern
import pickle
import csv
import pdb

import numpy as np
import matplotlib.pyplot as plt

from common import getDictSubset
from nameHistory import getMaxHeight

np.seterr("raise")

def alexaRanks():
    # failedDomains = []
    domains = []
    with open('top-1m.csv', 'r') as csvfile:
        reader = csv.reader(csvfile)
        for row in reader:
            rank = int(row[0])
            url = row[1]
            parsed_url = url[:url.index(".")]
            bitDomain = intern("d/" + parsed_url.lower())
            domains.append(bitDomain)
    return domains

def moving_average(a, n=3) :
    ret = np.cumsum(a, dtype=float)
    ret[n:] = ret[n:] - ret[:-n]
    return ret[n - 1:] / n

def variable_window_moving_average(x):
    cumulative = np.cumsum(x, dtype=float)
    ret = np.zeros(int((4/5) * (len(cumulative) - 1)))
    for i in range(len(ret)):
        lower = int((3/4) * (i + 1))
        upper = int((5/4) * (i + 1))
        ret[i] = (cumulative[upper] - cumulative[lower]) / (upper - lower)
    return ret

# def variable_window_moving_average(x):
#     cumulative = np.cumsum(x, dtype=float)
#     ret = np.zeros(int((3/4) * (len(cumulative) - 1)))
#     for i in range(len(ret)):
#         lower = int((2/3) * (i + 1))
#         upper = int((4/3) * (i + 1))
#         ret[i] = (cumulative[upper] - cumulative[lower]) / (upper - lower)
#     return ret
        

alexa_ranks = alexaRanks()
# Swap keys and values
# alexa_ranks = {rank: intern(name) for name, rank in alexa_ranks.items()}
# pdb.set_trace()
# alexa_list = []n
# for i in range(1, len(alexa_ranks) + 1):
#     alexa_list.append(alexa_ranks[i])

with open("nameDict.dat", "rb") as pickle_file:
    name_history = pickle.load(pickle_file)

max_height = getMaxHeight(name_history)
valid_names = getDictSubset(name_history,
                            lambda record: record.isValidAtHeight(max_height))
name_history = None
active_bit_names = getDictSubset(valid_names,
                                 lambda record: record.namespace() == "d")
valid_names = None

names = set(name for name in active_bit_names.keys())
active_bit_names = None
registered = [alexa_name in names for alexa_name in alexa_ranks]


averaged = variable_window_moving_average(registered)
pdb.set_trace()
plt.plot(range(1, len(averaged) + 1), averaged)
plt.ylim((0, 1.05))
plt.xscale("log")

# averaged = moving_average(registered, 10000)
# plt.plot(range(1, len(averaged) + 1), averaged)

# cumulative_prob = np.cumsum(registered) / np.array(range(1, len(registered) + 1))
# plt.plot(range(1, len(registered) + 1), cumulative_prob)
plt.show()
