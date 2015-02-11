#!/usr/bin/env python


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
	Abe.upgrade.find_namecoin_addresses(store)