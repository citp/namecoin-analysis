#!/usr/bin/env python3

import requests
import pdb

REQUEST_URL_PREFIX = "https://dotbit.me/get_domains_for_sale.php"

domains = []
i = 1
while True:
    params = {"p": 1}
    r = requests.get(REQUEST_URL_PREFIX, params = params)
    pdb.set_trace()
    if r.text is None:
        break
    print(r.text)
    i += 1
    


