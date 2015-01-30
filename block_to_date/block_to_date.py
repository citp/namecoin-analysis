#!/usr/bin/env python3

import requests
import json

from random import randint
from datetime import datetime
from pickle import dump

RPC_URL = "http://paul:alre2345nbcvsdfgoPDSF@localhost:8336"
DEFAULT_HEADERS = {'content-type': 'application/json'}


def get_block_height(request_id = None):
    if request_id is None:
        request_id = randint(0, 2**31)

    payload = {
        "method": "getblockcount",
        # "params": [214701],
        "jsonrpc": "2.0",
        "id": request_id,
    }
    response = requests.post(RPC_URL,
                             data=json.dumps(payload),
                             headers=DEFAULT_HEADERS).json()
    if response["error"] is None:
        return response["result"]

def get_block(blocknum, request_id = None):
    if request_id is None:
        request_id = randint(0, 2**31)

    payload = {
        "method": "getblockbycount",
        "params": [blocknum],
        "jsonrpc": "2.0",
        "id": request_id,
    }
    response = requests.post(
        RPC_URL, data=json.dumps(payload), headers=DEFAULT_HEADERS).json()
    return response["result"]

times = {}
for block_num in range(0, get_block_height() + 1):
    block = get_block(block_num)
    block_time = datetime.fromtimestamp(block["time"])
    times[block_num] = block_time

with open("block_times.pickle", "wb") as block_times_file:
    dump(times, block_times_file, protocol = 2)
