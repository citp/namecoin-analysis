#!/usr/bin/env bash

python3 transaction_edges.py --dbtype=psycopg2 --connect-args='{ "database": "abe" }' > transaction_edges.txt
