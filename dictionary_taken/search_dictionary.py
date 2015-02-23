#!/usr/bin/env python3

import gzip
import json

with gzip.open("names.txt.gz", "r") as names_file:
    names = json.loads(names_file.read().decode("utf-8"))

names = filter(lambda name: (name["name"].startswith("d/") and
                             "value" in name), names)
names = set(name["name"][2:] for name in names)

with open("/usr/share/dict/words", "r") as dictionary:
    dictionary_words = set(word.strip() for word in dictionary.readlines())

taken_dictionary_words = names & dictionary_words
percent_taken = 100 * (len(taken_dictionary_words) / len(dictionary_words))

print("There are " + str(len(dictionary_words)) + " words in this machines dictionary")
print("A total of " + str(len(taken_dictionary_words)) + " names are from the dictionary are taken.")
print("A total of " + str(percent_taken) + "% of words in the dictionary currently registered.")

