#!/usr/bin/env python3

from pickle import load
from datetime import date

import matplotlib.pyplot as plt
from matplotlib.dates import date2num

with open("block_times.pickle", "rb") as pickle_file:
    dates = load(pickle_file)

merge_mining_date = date(2011, 10, 8)
y_axis = list(range(0, max(dates.keys()) + 1))
x_axis = []

for i in y_axis:
    x_axis.append(dates[i])

plt.plot_date(x_axis, y_axis)
plt.ylabel("Block Number")
plt.xlabel("Date")
plt.annotate("Merge mining\nbegins", xy = (merge_mining_date, 20000),
             xytext=(date(2011, 5, 1), 40000),
             arrowprops=dict(facecolor='red', shrink=0.05))
plt.show()
    
