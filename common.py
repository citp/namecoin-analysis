#!/usr/bin/env python

import cPickle as pickle
import hashlib


class TransactionOutput(object):
    def __init__(self, height, tx_pos, txout_pos, from_pub_id, to_pub_id):
        self.height = height
        self.tx_pos = tx_pos
        self.txout_pos = txout_pos
        self.from_pub_id = from_pub_id
        self.to_pub_id = to_pub_id

class NameNew(TransactionOutput):
    def __init__(self, height, tx_pos, txout_pos, from_pub_id, to_pub_id, tx_hash):
        super(NameNew, self).__init__(height, tx_pos, txout_pos, from_pub_id, to_pub_id)
        self.tx_hash = tx_hash

    def __str__(self):
        return "NameNew({}, {}, {}, {})".format(self.height, self.tx_pos, self.from_pub_id, self.to_pub_id)

    def tx_type(self):
        return "new"

class NameUpdate(TransactionOutput):
    def __init__(self, height, tx_pos, txout_pos, from_pub_id, to_pub_id, name, value):
        super(NameUpdate, self).__init__(height, tx_pos, txout_pos, from_pub_id, to_pub_id)
        self.name = name
        self.value = value

    def __str__(self):
        return "NameUpdate({}, {}, {}, {}, {}, {})".format(self.height, self.tx_pos, self.from_pub_id, self.to_pub_id, self.name, self.value)

    def tx_type(self):
        return "update"

class NameFirstUpdate(NameUpdate):
    def __init__(self, height, tx_pos, txout_pos, from_pub_id, to_pub_id, name, tx_rand, value):
        super(NameFirstUpdate, self).__init__(height, tx_pos, txout_pos, from_pub_id, to_pub_id, name, value)
        self.tx_rand = tx_rand

    def __str__(self):
        return "NameFirstUpdate({}, {}, {}, {}, {}, {})".format(self.height, self.tx_pos, self.from_pub_id, self.to_pub_id, self.name, self.value)

    def tx_type(self):
        return "firstUpdate"



def load_object(filename):
    with open(filename, 'rb') as input:
        return pickle.load(input)

def save_object(obj, filename):
    with open(filename, 'wb') as output:
        pickle.dump(obj, output, pickle.HIGHEST_PROTOCOL)

def ripemd160(data):
    return hashlib.new("ripemd160", data)

def hash160(data):
    """A standard compound hash."""
    return ripemd160(hashlib.sha256(data).digest()).digest()
