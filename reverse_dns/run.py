#!/usr/bin/env python3

import gzip
import json
import pdb
from socket import gethostbyaddr, inet_pton, AF_INET, AF_INET6, herror
from pickle import dump

from dns.resolver import Resolver

DNS_SERVERS = ["75.127.14.107", "107.170.95.180"]

def ip_is_valid(ip, protocol):
    try:
        inet_pton(protocol, ip)
        return True
    except OSError:
        return False

def test_ips(ips, protocol):
    valid_ips = []
    for ip in ips:
        if ip_is_valid(ip, protocol):
            valid_ips.append(ip)
    return valid_ips

def resolve_ip(domain):
    resolver = Resolver()
    resolver.nameservers = DNS_SERVERS
    answer = resolver.query(domain)
    return [item.address for item in answer.rrset.items]


with gzip.open("names.txt.gz", "r") as names_file:
    names = json.loads(names_file.read().decode("utf-8"))

names = filter(lambda name: (name["name"].startswith("d/") and
                             "value" in name), names)

for name in names:
    try:
        value_info = json.loads(name["value"])
    except ValueError:
        continue
        
    if type(value_info) is not dict:
        continue

    if ("ns" in value_info and 
        len(value_info["ns"]) > 2 and
        "ns0.web-sweet-web.net" not in value_info["ns"]):
        pdb.set_trace()
pdb.set_trace()

dont_resolve = []
do_resolve = []
for name in names:
    try:
        value_info = json.loads(name["value"])
    except ValueError:
        continue

    if type(value_info) is not dict:
        continue

    valid_ips = []
    if "ip" in value_info:
        ips = value_info["ip"]
        if type(ips) is str:
            ips = [ips]
        valid_ips += test_ips(ips, AF_INET)
    if "ip6" in value_info:
        ips = value_info["ip6"]
        if type(ips) is str:
            ips = [ips]
        valid_ips += test_ips(ips, AF_INET6)

    if len(valid_ips) == 0:
        continue

    resolutions = []
    for ip in valid_ips:
        try:
            resolutions.append(gethostbyaddr(ip))
        except herror:
            continue

    if len(resolutions) > 0:
        do_resolve.append((name, resolutions))
    else:
        dont_resolve.append(name)


with open("dont_resolve.pickle", "wb") as dont_resolve_file:
    dump(dont_resolve, dont_resolve_file)

with open("do_resolve.pickle", "wb") as do_resolve_file:
    dump(do_resolve, do_resolve_file)

pdb.set_trace()
