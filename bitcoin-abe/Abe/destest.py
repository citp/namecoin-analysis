import deserialize
import binascii
from base58 import b58encode, hash_160_to_bc_address
import Abe.Chain.Namecoin
import Crypto.Hash.SHA256 as SHA256

import sys
import logging
import sqlite3
import pickle
import datetime

import Abe.DataStore
import Abe.readconf
import Abe.upgrade

logging.basicConfig(level=logging.DEBUG)
conf = {
    'chain_id': None,
    }
conf.update(Abe.DataStore.CONFIG_DEFAULTS)
args, argv = Abe.readconf.parse_argv(sys.argv[1:], conf, strict=False)

if argv and argv[0] in ('-h', '--help'):
    print("Usage: namecoin_dump.py --dbtype=MODULE --connect-args=ARGS")
elif argv:
    sys.stderr.write(
        "Error: unknown option `%s'\n"
        "See `namecoin_dump.py --help' for more information.\n"
        % (argv[0],))
else:
    store = Abe.DataStore.new(args)

script = "530c333438343139353934393239027b7d6d7576a90fee462a84eac99150b023fb941a266b88ac".decode("hex")

# i = 0
# opcode = 0
# while i < len(script):
#     vch = None
#     prevCode = opcode
#     opcode = ord(script[i])
#     i += 1
#     if opcode == 0x14 and prevCode == 0xa9:
#         break

# h160 = script[i:i+20]

# version='\x34'
# vh160 = version+h160
# h3=SHA256.new(SHA256.new(vh160).digest()).digest()
# addr=vh160+h3[0:4]

# print b58encode(addr)
# print binascii.hexlify(bytearray(h160))

decoded = [ x for x in deserialize.script_GetOp(script) ]

namechain = store.chains_by.id[3]

print namechain.parse_decoded_txout_script(decoded)
# print decoded