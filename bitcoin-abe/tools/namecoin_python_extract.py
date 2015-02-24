#!/usr/bin/env python
# Dump the Namecoin name data to standard output.

# Copyright(C) 2011 by Abe developers.

# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
# 
# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# Affero General Public License for more details.
# 
# You should have received a copy of the GNU Affero General Public
# License along with this program.  If not, see
# <http://www.gnu.org/licenses/agpl.html>.

import sys
import logging
import sqlite3
import pickle
import datetime

import Abe.DataStore
import Abe.readconf
from Abe.deserialize import script_GetOp, opcodes

import json

import matplotlib.pyplot as plt

NAME_NEW         = opcodes.OP_1
NAME_FIRSTUPDATE = opcodes.OP_2
NAME_UPDATE      = opcodes.OP_3
NAME_SCRIPT_MIN = '\x51'
NAME_SCRIPT_MAX = '\x54'
BLOCKS_TO_EXPIRE = 12000

execfile("../../common.py")

def iterate_name_updates(store, logger, chain_id):
    for height, tx_pos, txout_pos, from_pubkey_id, to_pubkey_id, script in store.selectall("""
          SELECT cc.block_height, bt.tx_pos, out1.txout_pos,
          out2.pubkey_id, out1.pubkey_id, out1.txout_scriptPubKey
          FROM chain_candidate cc
          JOIN block_tx bt ON (cc.block_id = bt.block_id)
          JOIN txout out1 ON (bt.tx_id = out1.tx_id)
          JOIN tx ON (tx.tx_id = out1.tx_id)
          JOIN txin ON (tx.tx_id = txin.tx_id)
          JOIN txout out2 ON (txin.txout_id = out2.txout_id)
          WHERE cc.chain_id = ?
          AND out1.txout_scriptPubKey >= ? AND out1.txout_scriptPubKey < ?
          AND ((out2.txout_scriptPubKey >= ? AND out2.txout_scriptPubKey < ?)
          OR (out1.txout_scriptPubKey >= ? AND out1.txout_scriptPubKey < ?))
          ORDER BY cc.block_height, bt.tx_pos, out1.txout_pos""",
                                     (chain_id, store.binin(NAME_SCRIPT_MIN),
                                      store.binin(NAME_SCRIPT_MAX), store.binin(NAME_SCRIPT_MIN),
                                      store.binin(NAME_SCRIPT_MAX), store.binin(NAME_SCRIPT_MIN),
                                      store.binin('\x52'))):
        height = int(height)
        tx_pos = int(tx_pos)
        txout_pos = int(txout_pos)
        tx_type = -1

        i = script_GetOp(store.binout(script))

        nameNewDict = {}

        try:
            name_op = i.next()[0]
            if name_op == NAME_NEW:
                tx_hash = i.next()[1]
                if tx_hash not in nameNewDict:
                    nameNewDict[tx_hash] = True
                    yield NameNew(height, tx_pos, txout_pos, from_pubkey_id, to_pubkey_id, tx_hash)
            elif name_op == NAME_FIRSTUPDATE:
                tx_type = 1
                raw_name = i.next()[1]
                name = raw_name.decode("ISO-8859-1")
                tx_rand = i.next()[1]
                value = i.next()[1]
                tx_hash = hash160(tx_rand + raw_name)
                yield NameFirstUpdate(height, tx_pos, txout_pos, from_pubkey_id, to_pubkey_id, name, tx_rand, value, tx_hash)
            elif name_op == NAME_UPDATE:
                raw_name = i.next()[1]
                name = raw_name.decode("ISO-8859-1")
                value = i.next()[1]
                yield NameUpdate(height, tx_pos, txout_pos, from_pubkey_id, to_pubkey_id, name, value)
            else:
                logger.warning("Unexpected first op: %s", repr(name_op))
                continue
        except StopIteration:
            logger.warning("Strange script at %d:%d:%d",
                           height, tx_pos, txout_pos)
            continue

def get_expiration_depth(height):
    if height < 24000:
        return 12000
    if height < 48000:
        return height - 12000
    return 36000

def dump(store, logger, chain_id):
    from collections import deque
    top = store.get_block_number(chain_id)
    expires = {}
    expiry_queue = deque()  # XXX unneeded synchronization

    for transactionOutput in iterate_name_updates(store, logger, chain_id):
        if transactionOutput.tx_type() == "new":
            continue

        height = transactionOutput.height
        tx_pos = transactionOutput.tx_pos
        txout_pos = transactionOutput.txout_pos
        name = transactionOutput.name
        value = transactionOutput.value
        is_first = (transactionOutput.tx_type() == "firstUpdate")
        while expiry_queue and expiry_queue[0]['block_id'] < height:
            e = expiry_queue.popleft()
            dead = e['name']
            if expires[dead] == e['block_id']:
                print(repr((e['block_id'], 'Expired', dead, None)))
        if expires.get(name, height) < height:
            type = 'Resurrected'
        elif is_first:
            type = 'First'
        else:
            type = 'Renewed'
        print(repr((height, type, name, value)))
        expiry = height + get_expiration_depth(height)
        expires[name] = expiry
        expiry_queue.append({'block_id': expiry, 'name': name, 'value': value})

    for e in expiry_queue:
        if expires[e['name']] > e['block_id']:
            pass
        elif e['block_id'] <= top:
            print(repr((e['block_id'], 'Expired', e['name'], None)))
        else:
            print(repr((e['block_id'], 'Until', e['name'], e['value'])))

def main(argv):
    logging.basicConfig(level=logging.DEBUG)
    conf = {
        'chain_id': None,
        }
    conf.update(Abe.DataStore.CONFIG_DEFAULTS)
    args, argv = Abe.readconf.parse_argv(argv, conf, strict=False)

    if argv and argv[0] in ('-h', '--help'):
        print("Usage: namecoin_dump.py --dbtype=MODULE --connect-args=ARGS")
        return 0
    elif argv:
        sys.stderr.write(
            "Error: unknown option `%s'\n"
            "See `namecoin_dump.py --help' for more information.\n"
            % (argv[0],))
        return 1

    store = Abe.DataStore.new(args)
    logger = logging.getLogger(__name__)
    if args.chain_id is None:
        row = store.selectrow(
            "SELECT chain_id FROM chain WHERE chain_name = 'Namecoin'")
        if row is None:
            raise Exception("Can not find Namecoin chain in database.")
        args.chain_id = row[0]

    a = datetime.datetime.now()

    nameInfos = []
    for x in iterate_name_updates(store, logger, args.chain_id):
        nameInfos.append(x)
    b = datetime.datetime.now()
    c = b - a
    print(c.total_seconds())

    save_object(nameInfos, "python_raw.dat")

    # for nameInfo in load_object("python_raw.dat"):
    #     print nameInfo.height, nameInfo.tx_type, nameInfo.name
    

    

    # xPoints = []
    # yPoints = []
    # total_registrations = 0

    # con = sqlite3.connect('example.db')
    # with con:
    #     cur = con.cursor()
    #     cur.execute("DROP TABLE IF EXISTS Names")
    #     cur.execute("CREATE TABLE Names(Id INTEGER PRIMARY KEY, name TEXT)")

    #     for x in iterate_name_updates(store, logger, args.chain_id):
    #         height, tx_pos, txout_pos, is_first, name, value = x
    #         if is_first is True:
    #             # total_registrations += 1
    #             # xPoints.append(height)
    #             # yPoints.append(total_registrations)
    #             # print height, total_registrations

    # plt.plot(xPoints, yPoints)
    # plt.ylabel('Total Updates')
    # plt.show()

    # dump(store, logger, args.chain_id)
    return 0

if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
