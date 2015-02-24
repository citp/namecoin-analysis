#!/usr/bin/env python3

from common import load_name_length, namelength_cost

name_length_histogram = load_name_length()
expected_cost = 0
total_registrations = float(sum(name_length_histogram.values()))

for length in name_length_histogram.keys():
    probability = name_length_histogram[length] / total_registrations
    expected_cost += probability * namelength_cost(length, base_price = 0.5)

print(expected_cost)
