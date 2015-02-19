#!/usr/bin/env python3

from decimal import Decimal
from collections import defaultdict

import networkx
import matplotlib.pyplot as plt
import pdb

edges_map = defaultdict(set)
with open("transaction_edges.txt", "r") as transaction_edges:
    for line in transaction_edges:
        edge = eval(line)
        try:
            input_address = int(edge[0])
            output_address = int(edge[1])
        except TypeError:
            continue
        edges_map[input_address].add(output_address)

graph = networkx.Graph()
for address in edges_map.keys():
    graph.add_node(address)

for input_address, output_addresses in edges_map.items():
    for output_address in output_addresses:
        graph.add_edge(input_address, output_address)
    edges_map[input_address] = None

networkx.draw(graph)
plt.savefig("graph_output.png")

