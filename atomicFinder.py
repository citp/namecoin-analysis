#!/usr/bin/env python3

import psycopg2


def cursor():
	conn = psycopg2.connect("dbname=abe user=postgres")
	return conn.cursor()

def findANTPYTransactions():
	namecoinTXQuery = """
	SELECT tx.tx_id, txout.pubkey_id
	FROM tx
	INNER JOIN txout ON (tx.tx_id = txout.tx_id)
	INNER JOIN txin ON (tx.tx_id = txin.tx_id)
	INNER JOIN txout txoutInput ON (txin.txout_id = txoutInput.txout_id)
	WHERE txoutInput.pubkey_id = txout.pubkey_id
	AND txoutInput.txout_scriptPubKey >= '52'
	AND txoutInput.txout_scriptPubKey < '54'
	AND (txout.txout_scriptPubKey < '51' OR txout.txout_scriptPubKey >= '54')
	"""

	cur = cursor()
	cur.execute(namecoinTXQuery)
	res = cur.fetchall()
	hashes = []
	for row in res:
		# Check whether the name also goes to the same pubkey
		cur.execute("SELECT * FROM txout WHERE tx_id = %s AND pubkey_id = %s AND txout_scriptPubKey >= '51' AND txout_scriptPubKey < '54'", row)
		match = cur.fetchall()
		if len(match) == 0:
			cur.execute("SELECT tx_hash FROM tx WHERE tx_id = %s ", [row[0]])
			txhash = cur.fetchall()
			hashes.append(txhash[0][0])
	return hashes

def findMultiOutputTransactions():
	namecoinTXQuery = """
	SELECT tx.tx_hash
	FROM txout
	JOIN tx ON (tx.tx_id = txout.tx_id)
	WHERE txout.tx_id in (
	SELECT tx_id
	FROM txout
	WHERE txout_scriptPubKey >= '53'
	AND txout_scriptPubKey < '54'
	)
	GROUP BY tx.tx_hash
	HAVING COUNT(*) >= 3
	ORDER BY tx.tx_hash
	"""
	cur = cursor()
	cur.execute(namecoinTXQuery)
	res = cur.fetchall()
	return [row[0] for row in res]

def getNameUpdateTransactions():
	namecoinTXQuery = """
	SELECT tx.tx_id, tx.tx_hash
	FROM tx
	JOIN txout ON (tx.tx_id = txout.tx_id)
	WHERE txout_scriptPubKey >= '53'
	AND txout_scriptPubKey < '54'
	"""
	cur = cursor()
	cur.execute(namecoinTXQuery)
	return cur.fetchall()


def scriptType(scriptPupKey):
	if scriptPupKey.startswith('51'):
		return True
	elif scriptPupKey.startswith('52'):
		return True
	elif scriptPupKey.startswith('53'):
		return True
	else:
		return False


def satoshiToCoin(satoshi):
	return float(satoshi) / 100000000

def getTXInfo(tx_id):
	cur = cursor()
	cur.execute("SELECT txout_value, txout_scriptPubKey, pubkey_id FROM txout WHERE tx_id = %s", [tx_id])
	outputs = cur.fetchall()

	cur.execute("SELECT txout_value, txout_scriptPubKey, pubkey_id FROM txin JOIN txout ON (txout.txout_id = txin.txout_id) WHERE txin.tx_id = %s", [tx_id])
	inputs = cur.fetchall()

	totalNonNameInput = 0
	totalNonNameOutput = 0

	for row in inputs:
		if not scriptType(row[1]):
			totalNonNameInput += row[0]

	for row in outputs:
		if not scriptType(row[1]):
			totalNonNameOutput += row[0]

	print("totalNonNameInput = ", satoshiToCoin(totalNonNameInput))
	print("totalNonNameOutput = ", satoshiToCoin(totalNonNameOutput))
	print("tip = ", satoshiToCoin(totalNonNameInput - totalNonNameOutput))
	print(inputs)
	print("\n\n", outputs)

def findAtomicTransactions():
	updateInfo = getNameUpdateTransactions()


# getTXInfo(1296159)

multi = findMultiOutputTransactions()
antpy = findANTPYTransactions()

both = [txhash for txhash in antpy if txhash in multi]
antpyonly = [txhash for txhash in antpy if txhash not in multi]
multionly = [txhash for txhash in multi if txhash not in antpy]

print("TX Hash in both ANTPY and Multi")
print("\n".join(both))

print("TX Hash in ANTPY only")
print("\n".join(antpyonly))

print("TX Hash in Multi only")
print("\n".join(multionly))

