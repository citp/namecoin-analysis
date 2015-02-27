#!/usr/bin/env python3

import sys
import logging
from listing import Listing
import pickle
from os import listdir

def load_object(filename):
    with open(filename, 'rb') as input:
        return pickle.load(input)

def save_object(obj, filename):
    with open(filename, 'wb') as output:
        pickle.dump(obj, output, pickle.HIGHEST_PROTOCOL)

def extractDomains(nameList):
	return list(map(lambda x: x.domain, nameList))


oldDomains = []
for f in listdir("scrape_data"):
	listings = load_object("scrape_data/" + f)
	domains = extractDomains(listings)
	addedDomains = [x for x in domains if x not in oldDomains]
	removedDomains = [x for x in oldDomains if x not in domains]

	if len(oldDomains) > 0:
		if len(addedDomains) > 0:
			print(f, "Added domains", addedDomains)
		if len(removedDomains) > 0:
			print(f, "Removed domains", removedDomains)

	oldDomains = domains

# list1 = extractDomains(nameList1)
# list2 = extractDomains(nameList2)
# firstList = extractDomains([x for x in list2 if x not in list1])
# print(firstList)

# print([listing.domain for listing in nameList if listing not in ])