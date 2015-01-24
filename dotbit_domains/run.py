#!/usr/bin/env python3

# Python std lib
import pdb
from re import finditer, search
from datetime import datetime
from time import sleep
from pickle import dump, HIGHEST_PROTOCOL
from os import makedirs
from os.path import join, exists

# 3rd party
import requests

# My stuff
from listing import Listing


REQUEST_URL_PREFIX = "https://dotbit.me/get_domains_for_sale.php"
# This regex looks ugly. Maybe fix it later.
REGEX = """<td>([a-zA-Z0-9-_]+\.bit)</td><td class=sp onclick='buyPrivateDomain\("[a-zA-Z0-9-_]+","Bitcoins","[0-9.-]+"\);'>([0-9-.]+)</td><td onclick='buyPrivateDomain\("[a-zA-Z0-9-_]+","Namecoins","[0-9.-]+"\);' class=sp>([0-9-]+)</td><td onclick='buyPrivateDomain\("[a-zA-Z0-9-_]+","Litecoins","[0-9.-]+"\);' class=sp>([0-9.-]+)</td>\s+<td onclick='buyPrivateDomain\("[a-zA-Z0-9-_]+","Peercoins","[0-9.-]+"\);' class=sp>([0-9.-]+)</td>\s*<td onclick='buyPrivateDomain\("[a-zA-Z0-9-_]+","Primecoins","[0-9.-]+"\);' class=sp>([0-9.-]+)</td>"""
OUTPUT_DIR = "scrape_data"

listings = []
i = 1
while True:
    if i % 10 == 0:
        print("Now fetching page " + str(i))
    params = {"p": i}
    r = requests.get(REQUEST_URL_PREFIX, params = params)
    if r.text is None or search(REGEX, r.text) is None:
        break
    for match in finditer(REGEX, r.text):
        domain = match.group(1)
        bitcoin_price = match.group(2)
        namecoin_price = match.group(3)
        litecoin_price = match.group(4)
        peercoin_price = match.group(5)
        primecoin_price = match.group(6)
        prices = {"bitcoin_price": bitcoin_price,
                  "namecoin_price": namecoin_price,
                  "litecoin_price": litecoin_price,
                  "peercoin_price": peercoin_price,
                  "primecoin_price": primecoin_price}
        listings.append(Listing(domain, prices, datetime.now()))
    i += 1
    sleep(0.5)
    
if not os.path.exists(OUTPUT_DIR):
    os.makedirs(OUTPUT_DIR)
filename = datetime.now().strftime("%Y-%m-%d-%H_%M.pickle")
with open(join(OUTPUT_DIR, filename), "wb") as output_file:
    dump(listings, output_file, protocol = HIGHEST_PROTOCOL)

