#!/usr/bin/env python3

from sys import intern
import pickle
import csv
import pdb

import numpy as np
import matplotlib.pyplot as plt
import tldextract

from common import getDictSubset
from nameHistory import getMaxHeight

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
names = None
alexa_ranks = None
pdb.set_trace()
