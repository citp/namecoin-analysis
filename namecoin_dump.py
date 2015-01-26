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

import Abe.DataStore
import Abe.readconf
from Abe.deserialize import script_GetOp, opcodes

NAME_NEW         = opcodes.OP_1
NAME_FIRSTUPDATE = opcodes.OP_2
NAME_UPDATE      = opcodes.OP_3
NAME_SCRIPT_MIN = '\x51'
NAME_SCRIPT_MAX = '\x54'
BLOCKS_TO_EXPIRE = 12000

def iterate_name_updates(store, logger, chain_id):


##"""
#            SELECT cc.block_height, bt.tx_pos, txout.txout_pos,
#            txout.txout_scriptPubKey
#            FROM chain_candidate cc
#            JOIN block_tx bt ON (cc.block_id = bt.block_id)
#            JOIN txout ON (bt.tx_id = txout.tx_id)
#            WHERE cc.chain_id = ?
#            AND txout_scriptPubKey >= ? AND txout_scriptPubKey < ?
#            ORDER BY cc.block_height, bt.tx_pos, txout.txout_pos""" 


    for height, from_pubkey_id, to_pubkey_id, script in store.selectall("""
          SELECT cc.block_height, out2.pubkey_id, out1.pubkey_id,
            out1.txout_scriptPubKey
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

        i = script_GetOp(store.binout(script))
        try:
            name_op = i.next()[0]
            if name_op == NAME_NEW:
                continue  # no effect on name map
            elif name_op == NAME_FIRSTUPDATE:
                
                is_first = True
                name = i.next()[1] #
                newtx_hash = i.next()[1]
                #rand = i.next()[1]  # XXX documented as optional; is it?
                value = i.next()[1]
            elif name_op == NAME_UPDATE:
                is_first = False
                name = i.next()[1]
                value = i.next()[1]
            else:
                logger.warning("Unexpected first op: %s", repr(name_op))
                continue
        except StopIteration:
            logger.warning("Strange script at %d:%d:%d",
                           height, from_pubkey_id, to_pubkey_id)
            continue
        yield (height, from_pubkey_id, to_pubkey_id, is_first, name, value)

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
    expiry_queue = deque() # XXX unneeded synchronization

    for x in iterate_name_updates(store, logger, chain_id):
        height, from_pubkey_id, to_pubkey_id, is_first, name, value = x
        while expiry_queue and expiry_queue[0]['block_id'] < height:
            e = expiry_queue.popleft()
            dead = e['name']
            if expires[dead] == e['block_id']:
                print repr((e['block_id'], 'Expired', dead, None, from_pubkey_id, to_pubkey_id))
        if expires.get(name, height) < height:
            type = 'Resurrected'
        elif is_first:
            type = 'First'
        else:
            type = 'Renewed'
        print repr((height, type, name, value, from_pubkey_id, to_pubkey_id))
        expiry = height + get_expiration_depth(height)
        expires[name] = expiry
        expiry_queue.append({'block_id': expiry, 'name': name, 'value': value})

    for e in expiry_queue:
        if expires[e['name']] > e['block_id']:
            pass
        elif e['block_id'] <= top:
            print repr((e['block_id'], 'Expired', e['name'], None, from_pubkey_id, to_pubkey_id))
        else:
            print repr((e['block_id'], 'Until', e['name'], e['value'], from_pubkey_id, to_pubkey_id))

def main(argv):
    logging.basicConfig(level=logging.DEBUG)
    conf = {
        'chain_id': None,
        }
    conf.update(Abe.DataStore.CONFIG_DEFAULTS)
    args, argv = Abe.readconf.parse_argv(argv, conf, strict=False)

    if argv and argv[0] in ('-h', '--help'):
        print "Usage: namecoin_dump.py --dbtype=MODULE --connect-args=ARGS"
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

    dump(store, logger, args.chain_id)
    return 0

if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
