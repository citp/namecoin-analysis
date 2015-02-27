#!/usr/bin/env python3

import sys
import logging

import matplotlib.pyplot as plt
from matplotlib.ticker import ScalarFormatter
from matplotlib.dates import YearLocator, MonthLocator, DateFormatter, date2num, AutoDateLocator
import numpy as np
import os.path
import operator
import collections
from IPy import IP
import re
import cProfile
import time
import json
from urllib.request import urlopen
from urllib.error import URLError, HTTPError
import http
import socket
import os
import random
from nltk.corpus import wordnet
from csv import DictReader
import itertools

from math import sqrt
from sklearn.feature_extraction import DictVectorizer as DV
from sklearn.svm import SVC
from sklearn.ensemble import RandomForestClassifier as RF
from sklearn.metrics import roc_auc_score as AUC
from sklearn.cross_validation import train_test_split
from sklearn import naive_bayes

from common import *
from segment_string import SegmentString

socket.setdefaulttimeout(10)

def getMaxHeight(nameDict):
    maxHeight = 0
    for name in nameDict:
        maxHeight = max(maxHeight, nameDict[name].latestOp().height)
    return maxHeight

def getCounts(nameDict, nameListFunc):
    bucketList = collections.defaultdict(int)
    for name in nameDict:
        bucketList[nameListFunc(nameDict[name])] += 1
    return bucketList

def isValidIp(ip):
    allowed = re.compile("([0-9]{1,3}\.){3}[0-9]{1,3}")
    return allowed.match(ip)

def dnsFields(op):
    serverFields = ["service", "ip", "ip6", "tor", "ip2", "freenet", "alias", "translate", "ns", "delegate", "import", "map"]
    dataFields = ["email", "loc", "info", "fingerprint", "tls", "ds"]
    json_object = op.jsonDict()
    if json_object:
        serverKeys = [key for key in list(set(json_object.keys()) & set(serverFields)) if len(json_object[key]) > 0]
        return filterValidDNSEntries({key:json_object[key] for key in json_object if key in serverKeys})
    else:
        return False

def latestValueDNSFields(record):
    serverFields = ["service", "ip", "ip6", "tor", "ip2", "freenet", "alias", "translate", "ns", "delegate", "import", "map"]
    dataFields = ["email", "loc", "info", "fingerprint", "tls", "ds"]
    json_object = record.latestValueJsonDict()
    if json_object:
        serverKeys = [key for key in list(set(json_object.keys()) & set(serverFields)) if not isinstance(json_object[key], int) and len(json_object[key]) > 0]
        return filterValidDNSEntries({key:json_object[key] for key in json_object if key in serverKeys})
    else:
        return []

def filterValidDNSEntries(json_object):
    fieldDict = {key: json_object[key] for key in json_object}
    if "map" in fieldDict:
        if isinstance(fieldDict["map"], dict):
            subdomains = list(fieldDict["map"].keys())
            for subdomain in subdomains:
                if isinstance(fieldDict["map"][subdomain], str):
                    if isPrivateIP(fieldDict["map"][subdomain]):
                        del fieldDict["map"][subdomain]
                elif isinstance(fieldDict["map"][subdomain], dict) :
                    fieldDict["map"][subdomain] = filterValidDNSEntries(fieldDict["map"][subdomain])
                    if not fieldDict["map"][subdomain]:
                        del fieldDict["map"][subdomain]
            if not fieldDict["map"]:
                del fieldDict["map"]
        else:
            del fieldDict["map"]

    if "ip" in fieldDict:
        if isinstance(fieldDict["ip"], str):
            if isPrivateIP(fieldDict["ip"]):
                del fieldDict["ip"]
        elif isinstance(fieldDict["ip"], list):
            fieldDict["ip"] = [ip for ip in fieldDict["ip"] if not isPrivateIP(ip)]
            if not fieldDict["ip"]:
                del fieldDict["ip"]
        else:
            del fieldDict["ip"]

    if "ns" in fieldDict:
        if isinstance(fieldDict["ns"], list):
            fieldDict["ns"] = [ns for ns in fieldDict["ns"] if isValidIp(ns) or is_valid_hostname(ns)]
            if not fieldDict["ns"]:
                del fieldDict["ns"]
        else:
            del fieldDict["ns"]

    return fieldDict

def isPrivateIP(ipAddressString):
    try:
        ipAddress = IP(ipAddressString)
        ipType = ipAddress.iptype()
        return ipType == "PRIVATE" or ipType == "LOOPBACK"
    except:
        return False

def getFullDNSRecord(valueDict, nameDict):
    if "delegate" in valueDict and valueDict["delegate"] in nameDict:
        delegateJSON = nameDict[valueDict["delegate"]].latestValueJsonDict()
        if delegateJSON:
            valueDict = getFullDNSRecord(delegateJSON)

    if "import" in valueDict:
        if isinstance(valueDict["import"], str) and valueDict["import"] in nameDict:
            importJSON = nameDict[nameImport].latestValueJsonDict()
            if importJSON:
                valueDict.update(getFullDNSRecord(importJSON))
        elif isinstance(nameImport, list):
            for importItem in nameImport:
                if importItem in nameDict:
                    importJSON = nameDict[nameImport].latestValueJsonDict()
                    if importJSON:
                        valueDict.update(getFullDNSRecord(importJSON))
        del valueDict["import"]                                                                                                        

def topValuesAtHeight(nameDict, height):
    ops = [json.dumps(dnsFields(nameDict[name].opAtHeight(height))) for name in nameDict if nameDict[name].opAtHeight(height)]
    counter = collections.Counter(ops)
    for value, count in counter.most_common():
        print(count, value)
    return

def possibleResolvableNames(nameDict):
    validNames = getDictSubset(nameDict, lambda record: record.isValidAtHeight(getMaxHeight(nameDict)))
    validBitNames = getDictSubset(validNames, lambda record: record.namespace() == "d")
    jsonValidBitNames = getDictSubset(validBitNames, lambda record: record.latestValueJson())
    jsonValidBitNamesWithRealInfo = getDictSubset(jsonValidBitNames, latestValueDNSFields)

    dnsFieldsDict = {name:latestValueDNSFields(nameDict[name]) for name in jsonValidBitNamesWithRealInfo}

    dnsFieldsDict = getDictSubset(dnsFieldsDict, lambda fieldDict: not (len(fieldDict) == 1 and "translate" in fieldDict and fieldDict["translate"].startswith("BM-")))
    dnsFieldsDict = getDictSubset(dnsFieldsDict, filterValidDNSEntries)



    dnsFields = [dnsFieldsDict[key] for key in dnsFieldsDict]
    counter = collections.Counter([json.dumps(fields) for fields in dnsFields])
    for value, count in counter.most_common():
        print(count, value)
    return

    byValueDict = collections.defaultdict(list)
    for name in dnsFieldsDict:
        byValueDict[json.dumps(latestValueDNSFields(nameDict[name]))].append(nameDict[name])

    names_to_check = [byValueDict[value][0] for value in byValueDict]
    domains_to_check = [domain.domainName() for domain in names_to_check]
    # print("Checking domains", len(names_to_check))
    # for domain in names_to_check:
    #     print(domain.name(), domain.latestValue())

    # ping = Pinger()
    # ping.thread_count = 16
    # ping.hosts = domains_to_check
    # reachable_domains = ping.start()

    # reachable_domains = load_object("reachable_domains.dat")

    # unreachable_names = [nameDict["d/" + host[:-4]] for host in reachable_domains['dead']]
    # reachable_names = [nameDict["d/" + host[:-4]] for host in reachable_domains['alive']]

    # print ("Unreachable Names")
    # for nameRecord in unreachable_names:
    #     print(nameRecord.name(), nameRecord.latestValue())

    # print ("\n\nReachable Names")
    # for nameRecord in reachable_names:
    #     print(nameRecord.name(), nameRecord.latestValue())

    # domainsToCurl = {}
    # for name in reachable_names:
    #     for value in byValueDict:
    #         if name in byValueDict[value]:
    #             domainsToCurl[value] = byValueDict[value]

    # i = 0
    # print("len(domainsToCurl) =", len(domainsToCurl))

    # a = 0
    # b = 0
    # c = 0
    # d = 0

    # subdirs = [x[0] for x in os.walk("front_pages2/")]
    # foldersToDelete = []                          
    # deletionDict = collections.defaultdict(set)
    # for subdir in subdirs:
    #     files = next(os.walk(subdir))[2] 
    #     d += 1                                                                            
    #     if (len(files) > 0):
    #         c += 1
    #         for aFile in files:
    #             if aFile.endswith(".bit.html"):
    #                 b += 1
    #                 name = 'd/' + aFile[:-9]
    #                 for value in domainsToCurl:
    #                     domainWithName = [record for record in domainsToCurl[value] if record.name() == name]
    #                     if domainWithName:
    #                         domainsToCurl[value].remove(domainWithName[0])
    #                         deletionDict[subdir].add(value)
    #                         a += 1
    # domainsToCurl = {domain:domainsToCurl[domain] for domain in domainsToCurl if domainsToCurl[domain]}

    # for folder in deletionDict:
    #     print(folder, len(deletionDict[folder]))

    # print(len(domainsToCurl))
    # print("Deleted", str(a))
    # print("Total files", str(b))
    # print(str(c))
    # print(str(d))
    # return

    # i = d - 1
    # for value in domainsToCurl:
    #     if value in deletionDict:
    #         folder = deletionDict[value].pop()
    #     else:
    #         folder = "front_pages2/" + str(i)
    #     for nameRecord in domainsToCurl[value]:
    #         if not os.path.exists(folder):
    #             os.makedirs(folder)
    #             i += 1
    #         downloadDomain(nameRecord.domainName(), folder)
        

    # print("total domains", len(dnsFieldsDict))
    # print("domains to curl", len(domainsToCurl))
    # print(reachable_domains['alive'])
    save_object(reachable_domains, "reachable_domains.dat")

def downloadDomain(domainName, folder):
    try:
        opened = urlopen('http://' + domainName)
    except HTTPError as e:
        print('Error code: ', e.code, 'for', domainName)
    except URLError as e:
        print("URLError", e.reason, 'for', domainName)
    except TimeoutError as e:
        print("Timed out for", domainName)
    except socket.timeout:
        print("Timed out for", domainName)
    except http.client.BadStatusLine as e:
        print("BadStatusLine", e, 'for', domainName)
    else:
        page = opened.read()
        if not domainName in opened.geturl():
            print(domainName, "goes to", opened.geturl())
        with open(folder + "/" + domainName + ".html", "wb") as text_file:
            text_file.write(page)

def jsonDictAnalysis(nameDict):
    validNames = getDictSubset(nameDict, lambda record: record.isValidAtHeight(getMaxHeight(nameDict)))
    validBitNames = getDictSubset(validNames, lambda record: record.namespace() == "d")
    jsonValidBitNames = getDictSubset(validBitNames, lambda record: record.latestValueJsonDict())
    counter = collections.Counter([field for name in jsonValidBitNames for field in jsonValidBitNames[name].latestValueJsonDict()])

    fieldDict = collections.defaultdict(list)
    for name in jsonValidBitNames:
        for field in jsonValidBitNames[name].latestValueJsonDict():
            fieldDict[field].append(name)

    # for field in fieldDict:
    #     print (len(fieldDict[field]), field)

    ipList = [name + " " + nameDict[name].latestValue() for name in fieldDict["alias"]]
    print("\n".join(ipList))
    # ipCounter = collections.Counter()

    # for (value, count) in ipCounter.most_common():
    #     print(count, value)

    # for name in fieldDict["alias"]:
    #     print(name, nameDict[name].latestValue())

def bitValueFrequencyAnalysis(nameDict):

    maxHeight = getMaxHeight(nameDict)

    queries = [
    lambda record: record.isValidAtHeight(maxHeight),
    lambda record: record.namespace() == "d",
    lambda record: record.latestValueJson(),
    latestValueDNSFields
    ]

    subsets = [nameDict]
    for i, query in enumerate(queries):
         subsets.append(getDictSubset(subsets[i], query))

    allCounts = [getCounts(subset, NameRecord.latestValue) for subset in subsets]

    # uniqueValidBitValues = getDictSubset(validBitJsonCountsWithRealInfo, lambda x: x <= 10)    
    # counts = getCounts(jsonValidBitNamesWithRealInfo, latestValueServerDNS)

    labels = ["total names", "total valid", "total valid bit", "total valid bit json", "total valid bit json with real info"]

    for label, subset, counts in zip(labels, subsets, allCounts):
        print("\n\n", label, len(subset), "unique", len(counts), "percentage", str(float(len(counts)) / float(len(subset))))
        for value, count in getTopValues(counts, 20):
            print(count, value)

def oneNameAnalysis(nameDict):
    oneName = getDictSubset(nameDict, lambda record: record.namespace() == "u")
    validOneName = getDictSubset(oneName, lambda record: record.isValidAtHeight(getMaxHeight(nameDict)))
    nonReserved = getDictSubset(validOneName, lambda record: "reservations@onename.io" not in record.latestValue())
    counts = getCounts(nonReserved, NameRecord.latestValue)
    uniqueValues = getDictSubset(counts, lambda x: x == 1)

    print("total u records:", len(oneName))
    print("valid u records:", len(validOneName))
    print("non reserved records", len(nonReserved))
    print("unique non reserved records", len(uniqueValues))

def findSquatterThreshold(nameDict):
    allValues = [x.value for name in nameDict for session in nameDict[name].sessions for x in session.valueChangingOps()]
    counter = collections.Counter(allValues)

    ignoreValues = set(["", "{}", "{\"ns\":[]}"])

    xData = []
    yData = []

    for i in range(5, 500):
        possibleSquatterValues = set([value for (value, count) in list(valuesOverN(counter, i))])
        xData.append(i)
        print(i)
        changeCount = 0
        for name in nameDict:
            for session in nameDict[name].sessions:
                squatter = None
                for op in session.valueChangingOps():
                    if op.value not in ignoreValues:
                        if op.value in possibleSquatterValues:
                            squatter = op.value
                        elif squatter:
                            changeCount += 1
                            squatter = None
        yData.append(changeCount)

    plt.plot(xData, yData)
    plt.show()

def findSquatterPurchases(nameDict):

    allValues = [x.value for name in nameDict for session in nameDict[name].sessions for x in session.valueChangingOps()]
    counter = collections.Counter(allValues)

    # print(counter['{"email":"virtcoin@gmail.com"}'])
    # print(counter['{"ip": "74.125.39.104", "info": { "status": "for sale" }, "map": {"": "74.125.39.104", "www": "74.125.39.104"}}'])
    # print(counter['{"ip":"1.2.3.4","email":"mailmeifyouwanttobuythisname@mail.ru","info":"Send an offer to: mailmeifyouwanttobuythisname@mail.ru"}'])
    # print(counter['{"ip":"127.0.0.1","map":{"*":{"ip":"127.0.0.1"}}}'])
    # return

    ignoreValues = set(["", "{}", "{\"ns\":[]}"])

    possibleSquatterValues = set([value for (value, count) in list(valuesOverN(counter, 10))])

    changesDict = collections.defaultdict(list)

    changeCount = 0

    changesTimeDict = collections.defaultdict(int)

    for name in nameDict:
        for session in nameDict[name].sessions:
            squatter = None
            for op in session.valueChangingOps():
                if op.value not in ignoreValues:
                    if op.value in possibleSquatterValues:
                        squatter = op.value
                    elif squatter:
                        changesDict[squatter].append((name, op.value))
                        changesTimeDict[op.height] += 1
                        changeCount += 1
                        squatter = None

    xData = []
    yData = []

    cumulativeTotal = 0
    for height in sorted(changesTimeDict):
        cumulativeTotal += changesTimeDict[height]
        xData.append(height)
        yData.append(cumulativeTotal)

    plt.plot(xData, yData)
    plt.show()

    for fromVal in changesDict:
        print("Changes from squatter", fromVal)
        for (name, toVal) in changesDict[fromVal]:
            print(name, toVal)
        print()

    print(changeCount)

def valueOccurenceTime(nameDict):
    xData = []
    yData = [[], [], [], []]
    stepSize = 1000
    buckets = [1000, 5]
    maxHeight = getMaxHeight(nameDict)
    blockTime = blockTimeDict()

    for height in range(0, maxHeight, stepSize):
        print(height)
        valueOps = [nameDict[name].opAtHeight(height) for name in nameDict]
        values = [x.value for x in valueOps if x is not None]
        counter = collections.Counter(values)

        yData[0].append(len([x for x in values if x == ""]))
        values = [x for x in values if x != ""]

        for index, occurences in enumerate(buckets): 
            topVals = set([value for value, count in valuesOverN(counter, occurences)])
            yData[index + 1].append(len([x for x in values if x in topVals]))
            values = [x for x in values if x not in topVals]

        yData[-1].append(len(values))
        xData.append(blockTime[height])
  
    plt.subplot(111)
    plt.plot(xData, yData[0], label="Blank values")

    for index, occurences in enumerate(buckets): 
        if not index:
            label = "Greater than " + str(occurences) + " occurences"
        else:
            label = "Between " + str(buckets[index - 1]) + " and " + str(occurences) + " occurences"
        plt.subplot(111)
        plt.plot(xData, yData[index + 1], label=label)
    plt.subplot(111)
    plt.plot(xData, yData[-1], label="Fewer than " + str(buckets[-1]) + " occurences")
    plt.legend(loc='upper left')
    plt.show()

def resurrectedAnalysis(nameDict):
    maxHeight = getMaxHeight(nameDict)
    bitNames = getDictSubset(nameDict, lambda record: record.namespace() == "d")
    currentNames = [name for name in bitNames if len(bitNames[name].sessions) > 1 and bitNames[name].isValidAtHeight(maxHeight)]
    print("Resurrected", len(currentNames))

    dotBitAlexa = set(alexaRanks())
    dirtyWords = [word.strip() for word in open('dirty.txt', 'r')]
    dirtyWords = set([word.lower() for word in dirtyWords if " " not in word])
    dictWords = set([word.strip() for word in open('/usr/share/dict/words', 'r')])
    bitWordList = set(["coin", "satoshi", "wallet", "crypto", "currency", "btc", "nmc", "blockchain"])

    unicodeNames = [name for name in currentNames if name.startswith("d/xn--")]
    currentNames = [name for name in currentNames if not name.startswith("d/xn--")]

    coinNames = [name for name in currentNames if any(word in name.lower() for word in bitWordList) or name.startswith("d/bit")]
    currentNames = [name for name in currentNames if not (any(word in name.lower() for word in bitWordList) or name.startswith("d/bit"))]

    numberNames = [name for name in currentNames if set(name[2:]).issubset(set("0123456789"))]
    currentNames = [name for name in currentNames if not set(name[2:]).issubset(set("0123456789"))]

    alexaNames = [name for name in currentNames if name.lower() in dotBitAlexa]
    currentNames = [name for name in currentNames if name.lower() not in dotBitAlexa]

    dirtyNames = [name for name in currentNames if any(dirtyWord in name.lower() for dirtyWord in dirtyWords)]
    currentNames = [name for name in currentNames if not any(dirtyWord in name.lower() for dirtyWord in dirtyWords)]

    shortNames = [name for name in currentNames if len(name[2:]) <= 3]
    currentNames = [name for name in currentNames if len(name[2:]) > 3]

    dictNames = [name for name in currentNames if wordnet.synsets(name[2:])]
    currentNames = [name for name in currentNames if not wordnet.synsets(name[2:])]

    for i in range(0, 1000):
        print(random.choice(currentNames))

    print("Unicode", len(unicodeNames))
    print("Coin", len(coinNames))
    print("Number", len(numberNames))
    print("Alexa", len(alexaNames))
    print("Dirty", len(dirtyNames))
    print("Short", len(shortNames))
    print("Dict", len(dictNames))
    print("Rest", len(currentNames))

def nonResurrectedAnalysis(nameDict):
    maxHeight = getMaxHeight(nameDict)
    bitNames = getDictSubset(nameDict, lambda record: record.namespace() == "d")
    currentNames = [name for name in bitNames if not bitNames[name].isValidAtHeight(maxHeight)]
    print("Non resurrected", len(currentNames))

    dotBitAlexa = set(alexaRanks())
    dirtyWords = [word.strip() for word in open('dirty.txt', 'r')]
    dirtyWords = set([word.lower() for word in dirtyWords if " " not in word])
    dictWords = set([word.strip() for word in open('/usr/share/dict/words', 'r')])
    bitWordList = set(["coin", "satoshi", "wallet", "crypto", "currency", "btc", "nmc", "blockchain"])

    unicodeNames = [name for name in currentNames if name.startswith("d/xn--")]
    currentNames = [name for name in currentNames if not name.startswith("d/xn--")]

    coinNames = [name for name in currentNames if any(word in name.lower() for word in bitWordList) or name.startswith("d/bit")]
    currentNames = [name for name in currentNames if not (any(word in name.lower() for word in bitWordList) or name.startswith("d/bit"))]

    numberNames = [name for name in currentNames if set(name[2:]).issubset(set("0123456789"))]
    currentNames = [name for name in currentNames if not set(name[2:]).issubset(set("0123456789"))]

    alexaNames = [name for name in currentNames if name.lower() in dotBitAlexa]
    currentNames = [name for name in currentNames if name.lower() not in dotBitAlexa]

    dirtyNames = [name for name in currentNames if any(dirtyWord in name.lower() for dirtyWord in dirtyWords)]
    currentNames = [name for name in currentNames if not any(dirtyWord in name.lower() for dirtyWord in dirtyWords)]

    shortNames = [name for name in currentNames if len(name[2:]) <= 3]
    currentNames = [name for name in currentNames if len(name[2:]) > 3]

    dictNames = [name for name in currentNames if wordnet.synsets(name[2:])]
    currentNames = [name for name in currentNames if not wordnet.synsets(name[2:])]


    print("Unicode", len(list(unicodeNames)))
    print("Coin", len(list(coinNames)))
    print("Number", len(list(numberNames)))
    print("Alexa", len(list(alexaNames)))
    print("Dirty", len(list(dirtyNames)))
    print("Short", len(list(shortNames)))
    print("Dict", len(list(dictNames)))
    print("Rest", len(list(currentNames)))

def partition(items, predicate=bool):
    yesList = []
    noList = []
    for item in items:
        (yesList if predicate(item) else noList).append(item)
    return yesList, noList

def currentNameBreakdown(nameDict):
    maxHeight = getMaxHeight(nameDict)
    bitNames = getDictSubset(nameDict, lambda record: record.namespace() == "d")
    currentNames = [name for name in bitNames if bitNames[name].isValidAtHeight(maxHeight)]

    dotBitAlexa = set(alexaRanks())
    dirtyWords = [word.strip() for word in open('dirty.txt', 'r')]
    dirtyWords = set([word.lower() for word in dirtyWords if " " not in word])
    dictWords = set([word.strip() for word in open('/usr/share/dict/words', 'r')])
    bitWordList = set(["coin", "satoshi", "wallet", "crypto", "currency", "btc", "nmc", "blockchain"])
    with open("name_lists/surnames.csv", "r") as surnames_file:
        reader = DictReader(surnames_file)
        surnamesSet = set(line["name"].lower() for line in reader)


    multipleOwner, currentNames = partition(currentNames, lambda name: len(nameDict[name].sessions) > 1)
    unicodeNames, currentNames = partition(currentNames, lambda name: name.startswith("d/xn--"))
    coinNames, currentNames = partition(currentNames, lambda name: any(word in name.lower() for word in bitWordList) or name.startswith("d/bit"))
    numberNames, currentNames = partition(currentNames, lambda name: set(name[2:]).issubset(set("0123456789")))
    alexaNames, currentNames = partition(currentNames, lambda name: name.lower() in dotBitAlexa)
    surnamesSet, currentNames = partition(currentNames, lambda name: name[2:].lower() in surnamesSet)
    dirtyNames, currentNames = partition(currentNames, lambda name: any(dirtyWord in name.lower() for dirtyWord in dirtyWords))
    shortNames, currentNames = partition(currentNames, lambda name: len(name[2:]) <= 3)
    dictNames, currentNames = partition(currentNames, lambda name: wordnet.synsets(name[2:]))
    multiWords, currentNames = partition(currentNames, lambda name: SegmentString().string_segments(name[2:]))

    # remaining = list(currentNames)

    # for i in range(0, 1000):
    #     print(random.choice(remaining))

    print("Multiple", len(multipleOwner))
    print("Unicode", len(unicodeNames))
    print("Coin", len(coinNames))
    print("Number", len(numberNames))
    print("Alexa", len(alexaNames))
    print("Dirty", len(dirtyNames))
    print("Short", len(shortNames))
    print("Dict", len(dictNames))
    print("Multiple words", len(multiWords))
    print("Rest", len(currentNames))


def nameClassifier(nameDict):

    maxHeight = getMaxHeight(nameDict)
    bitNames = getDictSubset(nameDict, lambda record: record.namespace() == "d")

    dotBitAlexa = set(alexaRanks())
    dirtyWords = [word.strip() for word in open('dirty.txt', 'r')]
    dirtyWords = set([word.lower() for word in dirtyWords if " " not in word])
    dictWords = set([word.strip() for word in open('/usr/share/dict/words', 'r')])
    bitWordList = set(["coin", "satoshi", "wallet", "crypto", "currency", "btc", "nmc", "blockchain"])

    xData = []
    yData = []

    feature_names = np.array(["inAlexa", "inDict", "inDirty", "isNumber", "length", "coinRelated"])

    for name in bitNames:
        xData.append([
            int(name in dotBitAlexa) + 1,                                                       # inAlexa
            int(len(wordnet.synsets(name[2:])) >= 1) + 1,                                       # inDict
            int(any(dirtyWord in name.lower() for dirtyWord in dirtyWords)) + 1,                # inDirty
            int(set(name[2:]).issubset(set("0123456789"))) + 1,                                 # isNumber
            len(name),                                                                          # length
            int(any(word in name.lower() for word in bitWordList) or name.startswith("d/bit")) + 1 # coinRelated
        ])
        yData.append(int(bitNames[name].isValidAtHeight(maxHeight)))


    x_train, x_test, y_train, y_test = train_test_split(xData, yData, test_size=.10, random_state=33)

    mnb = naive_bayes.MultinomialNB()
    mnb.fit(x_train, y_train)
    print("Accuracy", mnb.score(x_test, y_test))

    # rf = RF(n_estimators=1, criterion='entropy', max_features='auto', max_depth=20, bootstrap=True, oob_score=True, n_jobs=2, random_state=33)
    # rf = rf.fit(x_train, y_train)

    # importances = rf.feature_importances_
    # print(feature_names)
    # print(importances)
    # important_names = feature_names[importances > np.mean(importances)]
    # print(important_names)

    # p = rf.predict_proba(x_test)
    # auc = AUC(y_test, p[:,1])

    print("RF AUC", auc)

def valueOccurrenceHist(nameDict, height):
    valueOps = [nameDict[name].opAtHeight(height) for name in nameDict]
    values = [x.value for x in valueOps if x is not None]
    counter = collections.Counter(values)
    counts = [counter[value] for value in values]

    print(len(values), "at height", height)

    fig = plt.figure()
    ax = fig.add_subplot(111)
    ax.hist(counts, bins = 10 ** np.linspace(0, np.log10(60000), 50))
    ax.semilogx()
    for axis in [ax.xaxis, ax.yaxis]:
        axis.set_major_formatter(ScalarFormatter())
    plt.ylim([0,50000])

def rankByFunc(nameDict, nameRecordValue, higherIsBetter):
    nameRawValues = {name:nameRecordValue(nameDict[name]) for name in nameDict}

    nameRanks = {}

    rank = 1

    prevUpdates = None

    for (name, value) in sorted(nameRawValues.items(), key=lambda x: x[1], reverse=higherIsBetter):
        if not prevUpdates:
            nameRanks[name] = rank
            prevUpdates = value
        else:
            if value < prevUpdates:
                rank = len(nameRanks) + 1
                prevUpdates = value
            nameRanks[name] = rank
            
    i = 0
    for (name, value) in sorted(nameRanks.items(), key=lambda x: x[1]):
        print(name, value, nameRawValues[name])
        i += 1
        if i > 1000:
            break
    return nameRanks

def rankNumberOfValueChanges(nameDict):
    rankByFunc(nameDict, lambda record: record.numberOfValueChanges(), True)

def rankIsAlive(nameDict):
    maxHeight = getMaxHeight(nameDict)
    rankByFunc(nameDict, lambda record: int(record.isValidAtHeight(maxHeight)), True)

def rankJSONDict(nameDict):
    maxHeight = getMaxHeight(nameDict)
    rankByFunc(nameDict, lambda record: int(record.latestValueJsonDict()), True)

def rankValidDNSDict(nameDict):
    maxHeight = getMaxHeight(nameDict)
    rankByFunc(nameDict, lambda record: int(len(latestValueDNSFields(record)) > 0), True)


def alexaAnalysis(nameDict, blockTime):
    xData = []
    yData = []
    dotBitAlexa = alexaRanks()

    bucketsValues = [0, 1000, 10000, 100000, 500000, 1000000]
    buckets = []
    labels = []
    for i, start in enumerate(bucketsValues[:-1]):
        alexa_names = set([key for key, value in dotBitAlexa.items() if start <= value <= bucketsValues[i + 1]])
        xData = []
        for name in alexa_names:
            if name in nameDict:
                firstSession = nameDict[name].sessions[0]
                xData.append(date2num(blockTime[firstSession.firstUpdate.height]))
        buckets.append(xData)
        labels.append("Alexa " + str(start) + " to " + str(bucketsValues[i + 1]))

    fig = plt.figure()
    ax = fig.add_subplot(111)

    ax.hist(buckets, 100, stacked=True, label=labels, cumulative=True)

    months = MonthLocator(range(1, 13), bymonthday=1, interval=4)
    monthsFmt = DateFormatter("%b '%y")

    ax.xaxis.set_major_locator(months)
    ax.xaxis.set_major_formatter(monthsFmt)
    ax.xaxis.set_minor_locator(MonthLocator())
    ax.format_xdata = DateFormatter('%m-%d-%Y')


    ax.grid(True)
    fig.autofmt_xdate()
    ax.legend()

    # alexa_names = set([key for key, value in dotBitAlexa.items() if value <= 10000])
    # for name in alexa_names:
    #     if name in nameDict:
    #         nameRecord = nameDict[name]
    #         firstSession = nameRecord.sessions[0]
    #         xData.append(dotBitAlexa[name])
    #         yData.append(blockTime[firstSession.firstUpdate.height])

    # plt.scatter(xData, yData)

    plt.show()

def main(argv):

    rawNameDict = {}
    nameNewDict = {}

    if not os.path.isfile("nameDict.dat"):
        dataList = load_object("python_raw.dat")

        for nameInfo in dataList:
            if nameInfo.isNew():
                nameNewDict[nameInfo.tx_hash] = nameInfo

        for nameInfo in dataList:
            if nameInfo.isFirstUpdate():
                name = nameInfo.name
                tx_hash = nameInfo.tx_hash
                if tx_hash in nameNewDict:
                    if name in rawNameDict:
                        rawNameDict[name].append(nameNewDict[tx_hash])
                    else:
                        rawNameDict[name] = [nameNewDict[tx_hash]]
                    del nameNewDict[tx_hash]
                    rawNameDict[name].append(nameInfo)
                else:
                    print("Error, can't find matching new for firstupdate", name)
            elif nameInfo.isUpdate():
                rawNameDict[nameInfo.name].append(nameInfo)

        nameDict = {name:NameRecord(rawNameDict[name]) for name in rawNameDict}

        save_object(nameDict, "nameDict.dat")
        # save_object(nameNewDict.values(), "unusedNameNew.dat")
    else:
        nameDict = load_object("nameDict.dat")
        # nameNewDict = load_object("unusedNameNew.dat")


    # blockTime = blockTimeDict()
    # alexaAnalysis(nameDict, blockTime)

    # for i in [1000, 10000, 25000, 50000, 100000, 125000, 150000, 175000, 200000, getMaxHeight(nameDict)]:
    #     valueOccurrenceHist(nameDict, i) 
    #     plt.savefig("test/occurenceHist2_" + str(i) + ".png")
    #     plt.clf()

    rankValidDNSDict(nameDict)

    # currentNameBreakdown(nameDict)

    # resurrectedAnalysis(nameDict)
    # nonResurrectedAnalysis(nameDict)

    # findSquatterPurchases(nameDict)
    # cProfile.run('valueOccurenceTime(nameDict)')

    # bitValueFrequencyAnalysis(nameDict)

    # valueOccurenceTime(nameDict)

    # oneNameAnalysis(nameDict)

    # possibleResolvableNames(nameDict)

    # bitNames = getDictSubset(nameDict, lambda record: record.namespace() == "d")
    # topValuesAtHeight(bitNames, 140000)

    # valueList = [record.value for name in nameDict for record in nameDict[name] if record.hasValue()]
    # counter = collections.Counter(valueList)

    # print("\n".join([str(count) + " " + str(value) for (value, count) in counter.most_common(250)]))

    # valueCounts = getCounts(nameDict, NameRecord.latestValue)
    # validNames = getDictSubset(nameDict, lambda record: record.isValidAtHeight(getMaxHeight(nameDict)))
    # valueCountsByNamespace = getCounts(validNames, lambda x : "Namespace " + getNamespace(x) + ": " + x.latestValue())
    # namespaceCount = getCounts(validNames, getNamespace)

    # for value, count in getTopValues(namespaceCount, 20):
    #     print(count, value)

    # for value, count in getTopValues(valueCountsByNamespace, 50):
    #     print(count, value)



    # updateCount = getCounts(nameDict, getNumberOfNameTransactions)
    # changeUpdateCount = getCounts(nameDict, getNumberOfValueChanges)
    # ownerChangeCount = getCounts(nameDict, getNumberOfOwnerChanges)

    # print "Name Transactions"
    # for length in updateCount:
    #     print length, updateCount[length]

    # print "Value Changes"
    # for length in changeUpdateCount:
    #     print length, changeUpdateCount[length]

    # print "Owner Changes"
    # for length in ownerChangeCount:
    #     print length, ownerChangeCount[length]
    
if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
