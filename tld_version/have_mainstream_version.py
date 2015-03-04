#!/usr/bin/env python3
from socket import gethostbyname, gaierror
from collections import deque
from threading import Thread
from queue import Queue
from sys import intern

import pickle
import os.path

VARIANTS = [".com", ".net", ".org"]

def save_resolutions(resolutions):
    with open("name_check_results.pickle", "wb") as output_file:
        pickle.dump(resolutions, output_file)

def check_name(name, q):
    results = dict()
    for tld in VARIANTS:
        try:
            results[tld] = intern(gethostbyname(name + tld))
        except gaierror:
            results[tld] = False
        except UnicodeError as e:
            results = {tld : False for tld in VARIANTS}
            results["Error"] = e
            continue
        except Exception as e:
            # print(name)
            # print(e)
            results[tld] = e
            results["Error"] = True
    q.put((name, results))

def process_threads(threads, result_queue, resolutions):
        while len(threads) > 0:
            thread = threads.popleft()
            thread.join()
        while not result_queue.empty():
            name, results = q.get()
            resolutions[name] = results

with open("names_to_check.pickle", "rb") as name_file:
    names_to_check = pickle.load(name_file)

if os.path.isfile("name_check_results.pickle"):
    with open("name_check_results.pickle", "rb") as check_results_file:
        resolutions = pickle.load(check_results_file)
else:
    resolutions = dict()

q = Queue()
threads = deque()

for i, name in enumerate(names_to_check):
    if i % 1000 is 0 and i > 0:
        process_threads(threads, q, resolutions)
        save_resolutions(resolutions)
        print(i)
    if "." in name:
        resolutions[name] = {"Error": "'.' in name"} 
        continue
    if name in resolutions.keys():
        continue
    t = Thread(target=check_name, args=(name, q))
    t.daemon = True
    threads.append(t)
    t.start()


process_threads(threads, q, resolutions)
save_resolutions(resolutions)
print("Done resolving.")
            

