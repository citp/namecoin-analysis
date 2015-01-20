# namecoin-analysis
Doing analysis of Namecoin blockchain

To create bitcoin-abe database:
python -m Abe.abe --config=abe-pg.conf

To generate namecoin data:
./namecoin_dump.py --dbtype=psycopg2 --connect-args='{ "database": "abe" }' > namecoin_tx.txt