# namecoin-analysis
Doing analysis of Namecoin blockchain


To generate namecoin data:
./namecoin_dump.py --dbtype=psycopg2 --connect-args='{ "database": "abe" }' > namecoin_tx.txt