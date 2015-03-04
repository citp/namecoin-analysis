#!/usr/bin/env python3
from socket import gethostbyname, gaierror
from collections import defaultdict
import pickle

# from nameHistory import getDictSubset

VARIANTS = [".com", ".net", ".org"]

with open("names_to_check.pickle", "rb") as name_file:
    names_to_check = pickle.load(name_file)

# validBitNames = getDictSubset(name_dict, lambda record: record.namespace() == "d")

# names_to_check = [name[2:] for name in validBitNames.keys()]
# with open("bit_names.pickle", "wb") as name_file:
#    pickle.dump(names_to_check, name_file)

resolutions = defaultdict(dict)

for i, name in enumerate(names_to_check):
    if i % 1000 is 0:
        print(i)
    if "." in name:
        continue
    for tld in VARIANTS:
        try:
            gethostbyname(name)
            resolutions[name][tld] = True
        except gaierror:
            resolutions[name][tld] = False
        except UnicodeError as e:
            resolutions[name] = {tld : False for tld in VARIANTS}
            resolutions[name]["Error"] = e
            continue
        except Exception as e:
            print(name)
            print(e)
            resolutions[name][tld] = e
            resolutions["Error"] = True
            
with open("name_check_results.pickle", "wb") as output_file:
    pickle.dump(resolutions, output_file)
