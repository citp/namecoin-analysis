#!/usr/bin/env python3

from common import load_name_length
from random import shuffle

name_length_histogram = load_name_length()

def normal_fee_counts(x_min = 0, x_max = 1000):
    return [float(x) / 0.02 for x in range(x_min, x_max)]

def escrow_counts(escrow_cost = 200, x_min = 0, x_max = 1000):
    return [float(x) / (escrow_cost + 0.005) for x in range(x_min, x_max)]

def namelength_cost(name, base_price = 10):
    name_length = len(name)
    if name_length <= 3:
        return 5 * base_price
    elif name_length <= 6:
        return 2 * base_price
    elif name_length <= 14:
        return 0.5 * base_price
    elif name_length <= 20:
        pass
    else:
    
def namelength_counts(x_min = 0, x_max = 1000):
    elements = shuffle(name_length_histogram)
    count = []
    current_element_index = 0
    for x in range(0, 1000):
        
