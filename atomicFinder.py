#!/usr/bin/env python3

import psycopg2

namecoinTXQuery = """
SELECT tx.tx_id, txout.pubkey_id
FROM tx
INNER JOIN txout ON (tx.tx_id = txout.tx_id)
INNER JOIN txin ON (tx.tx_id = txin.tx_id)
INNER JOIN txout txoutInput ON (txin.txout_id = txoutInput.txout_id)
WHERE txoutInput.pubkey_id = txout.pubkey_id
AND txoutInput.txout_scriptPubKey >= '51'
AND txoutInput.txout_scriptPubKey < '54'
AND txout.txout_value > 5000000
"""

conn = psycopg2.connect("dbname=abe user=postgres")
cur = conn.cursor()
cur.execute(namecoinTXQuery)
res = cur.fetchall()
for row in res:
	cur.execute("SELECT * FROM txout WHERE tx_id = %s AND pubkey_id = %s AND txout_scriptPubKey >= '51' AND txout_scriptPubKey < '54'", row)
	match = cur.fetchall()
	if len(match) == 0:
		cur.execute("SELECT tx_hash FROM tx WHERE tx_id = %s ", [row[0]])
		txhash = cur.fetchall()
		print(txhash[0][0])
