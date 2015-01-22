#!/usr/bin/env python3

import requests
import json
from random import randint

from transaction import Transaction


RPC_URL = "http://paul:alre2345nbcvsdfgoPDSF@localhost:8336"
DEFAULT_HEADERS = {'content-type': 'application/json'}

def get_block_height():
    payload = {
        "method": "getblockcount",
        # "params": [214701],
        "jsonrpc": "2.0",
        "id": 0,
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

def tx_hash_to_transaction(tx_hash, request_id = None):
    if request_id is None:
        request_id = randint(0, 2**31)

    payload = {
        "method": "getrawtransaction",
        "params": [tx_hash],
        "jsonrpc": "2.0",
        "id": request_id,
    }
    response = requests.post(
        RPC_URL, data=json.dumps(payload), headers=DEFAULT_HEADERS).json()

    raw_transaction = response["result"]

    payload = {
        "method": "decoderawtransaction",
        "params": [raw_transaction],
        "jsonrpc": "2.0",
        "id": request_id,
    }

    response = requests.post(
        RPC_URL, data=json.dumps(payload), headers=DEFAULT_HEADERS).json()    

    return Transaction(response["result"])

block_height = get_block_height()
transactions = []
for i in range(0, block_height):
    block = get_block(i, i)
    for tx_hash in block["tx"]:
        transaction = tx_hash_to_transaction(tx_hash)
        transactions.append(transaction)
    if i % 1000 == 0:
        print(i)
        print(len(transactions))

# response = requests.post(
#     url, data=json.dumps(payload), headers=headers).json()


