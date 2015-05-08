#!/usr/bin/env python3

import sys
import matplotlib.pyplot as plt
from matplotlib.ticker import ScalarFormatter, FuncFormatter
from matplotlib.dates import MonthLocator, DateFormatter, date2num
import matplotlib.pyplot as plt
from matplotlib import rc, rcParams
from collections import Counter
import numpy as np
import os.path
import collections
from IPy import IP
import re
import json
from urllib.request import urlopen
from urllib.error import URLError, HTTPError
import threading
import queue
import http
import socket
import os
import ssl
import random
from nltk.corpus import wordnet
from csv import DictReader

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

def dnsFields(op, nameDict):
    serverFields = ["ip", "ip6", "alias", "ns", "delegate", "import", "map", "freenet", "ip2", "tor", "service", "translate"]  
    # dataFields = ["email", "loc", "info", "fingerprint", "tls", "ds"]
    json_object = op.jsonDict()
    if json_object:
        getFullDNSRecord(json_object, nameDict)
        serverKeys = [key for key in list(set(json_object.keys()) & set(serverFields)) if not isinstance(json_object[key], int) and len(json_object[key]) > 0]
        return filterValidDNSEntries({key:json_object[key] for key in json_object if key in serverKeys})
    else:
        return []

def onlyUsedTop(fields):
    # getFullDNSRecord(fields, nameDict)
    if "ns" in fields and len(fields["ns"]) > 0 and isinstance(fields["ns"], list):
        return {"ns" : fields["ns"]}
    elif "ip" in fields:
        return {"ip" : fields["ip"]}
    elif "ip6" in fields:
        return {"ip6" : fields["ip6"]}
    elif "tor" in fields:
        return {"tor" : fields["tor"]}
    elif "alias" in fields:
        return {"alias" : fields["alias"]}
    elif "map" in fields:
        if isinstance(fields["map"], dict):
            if "" in fields["map"]:
                if isinstance(fields["map"][""], dict):
                    res = onlyUsedTop(fields["map"][""])
                    if res:
                        return res
                elif isinstance(fields["map"][""], str):
                    return {"ip" : fields["map"][""]}
    elif "translate" in fields:
        return {"translate" : fields["translate"]}
    return fields

def recordType(fields):
    if "ns" in fields and len(fields["ns"]) > 0 and isinstance(fields["ns"], list):
        for ns in fields["ns"]:
            if isValidIp(ns) and not isPrivateIP(ns):
                return "NS_IP"
        return "NS_NAME"
    elif "ip" in fields:
        if isinstance(fields["ip"], str):
            return "IP_SINGLE"
        elif isinstance(fields["ip"], list):
            if len(fields["ip"]) == 1:
                return "IP_SINGLE"
            else:
                return "IP_MULTIPLE"
    elif "ip6" in fields:
        if isinstance(fields["ip6"], str):
            return "IP6_SINGLE"
        elif isinstance(fields["ip6"], list):
            if len(fields["ip6"]) == 1:
                return "IP6_SINGLE"
            elif len(fields["ip6"]) > 1:
                return "IP6_MULTIPLE"
    elif "tor" in fields:
        return "TOR"
    elif "alias" in fields:
        return "ALIAS"
    elif "map" in fields:
        if isinstance(fields["map"], dict):
            if "" in fields["map"]:
                if isinstance(fields["map"][""], dict):
                    res = recordType(fields["map"][""])
                    if res:
                        return res
                elif isinstance(fields["map"][""], str):
                    return "IP_SINGLE"
    elif "translate" in fields:
        return "TRANSLATE_ONLY"
    return "ONLY_SUB"


def latestValueDNSFields(record, nameDict):
    return dnsFields(record.latestOp(), nameDict)

def filterValidDNSEntries(json_object):
    serverFields = ["ip", "ip6", "alias", "ns", "delegate", "import", "map", "freenet", "ip2", "tor", "service", "translate"]
    fieldDict = {key: json_object[key] for key in json_object if key in serverFields}
    if "map" in fieldDict:
        if isinstance(fieldDict["map"], dict):
            subdomains = list(fieldDict["map"].keys())
            for subdomain in subdomains:
                if "_" in subdomain:
                    del fieldDict["map"][subdomain]
                elif isinstance(fieldDict["map"][subdomain], str):
                    if isPrivateIP(fieldDict["map"][subdomain]):
                        del fieldDict["map"][subdomain]
                elif isinstance(fieldDict["map"][subdomain], dict):
                    fieldDict["map"][subdomain] = filterValidDNSEntries(fieldDict["map"][subdomain])
                    if not fieldDict["map"][subdomain]:
                        del fieldDict["map"][subdomain]
                elif isinstance(fieldDict["map"][subdomain], list):
                    del fieldDict["map"][subdomain]
            if not fieldDict["map"]:
                del fieldDict["map"]
        else:
            del fieldDict["map"]

    if "ip" in fieldDict:
        if not len(fieldDict["ip"]):
            del fieldDict["ip"]
        elif isinstance(fieldDict["ip"], str):
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
            fieldDict["ns"] = [ns for ns in fieldDict["ns"] if (isValidIp(ns) and not isPrivateIP(ns)) or is_valid_hostname(ns)]
            if not fieldDict["ns"]:
                del fieldDict["ns"]
        else:
            del fieldDict["ns"]

    if "alias" in fieldDict:
        if not fieldDict["alias"]:
            del fieldDict["alias"]

    if "translate" in fieldDict:
        if not is_valid_hostname(fieldDict["translate"]):
            del fieldDict["translate"]

    return fieldDict

def isPrivateIP(ipAddressString):
    try:
        ipAddress = IP(ipAddressString)
        ipType = ipAddress.iptype()
        return ipType == "PRIVATE" or ipType == "LOOPBACK"
    except:
        return False

def getFullDNSRecord(valueDict, nameDict):
    if "delegate" in valueDict:
        if isinstance(valueDict["delegate"], str) and valueDict["delegate"] in nameDict:
            delegateJSON = nameDict[valueDict["delegate"]].latestValueJsonDict()
            if delegateJSON:
                getFullDNSRecord(delegateJSON, nameDict)
                valueDict.clear()
                valueDict.update(delegateJSON)
        elif isinstance(valueDict["delegate"], list):
            for delegate in valueDict["delegate"]:
                if isinstance(delegate, str):
                    if delegate in nameDict:
                        delegateJSON = nameDict[delegate].latestValueJsonDict()
                        if delegateJSON:
                            getFullDNSRecord(delegateJSON, nameDict)
                            valueDict.clear()
                            valueDict.update(delegateJSON)
                    else:
                        del valueDict["delegate"]

    if "import" in valueDict:
        if isinstance(valueDict["import"], str) and valueDict["import"] in nameDict:
            importJSON = nameDict[valueDict["import"]].latestValueJsonDict()
            if importJSON:
                getFullDNSRecord(importJSON, nameDict)
                valueDict.update(importJSON)
        # elif isinstance(valueDict["import"], list):
        #     for importItem in valueDict["import"]:
        #         if importItem in nameDict:
        #             importJSON = nameDict[importItem].latestValueJsonDict()
        #             if importJSON:
        #                 valueDict.update(getFullDNSRecord(importJSON))
        del valueDict["import"]                                                                                                        

def topValuesAtHeight(nameDict, height):
    ops = [json.dumps(dnsFields(nameDict[name].opAtHeight(height))) for name in nameDict if nameDict[name].opAtHeight(height)]
    counter = collections.Counter(ops)
    for value, count in counter.most_common():
        print(count, value)
    return

def getRedirects():
    with open('curlErrors.dat', 'rb') as file:
        errors = pickle.load(file)
    list1, list2 = zip(*errors["Redirection"])
    for domain in list1:
        try:
            opened = urlopen('http://' + domain)
            with open('curl_test/' + domain + ".html", "wb") as text_file:
                text_file.write(opened.read())
        except:
            continue

def possibleResolvableNames(nameDict):
    maxHeight = getMaxHeight(nameDict)
    validNames = getDictSubset(nameDict, lambda record: record.isValidAtHeight(maxHeight))
    validBitNames = getDictSubset(validNames, lambda record: record.namespace() == "d")
    print(len(validBitNames))
    jsonValidBitNames = getDictSubset(validBitNames, lambda record: record.latestValueJsonDict())
    print(len(jsonValidBitNames))
    jsonValidBitNamesWithRealInfo = getDictSubset(jsonValidBitNames, latestValueDNSFields)
    print(len(jsonValidBitNamesWithRealInfo))

    dnsFieldsDict = {name:latestValueDNSFields(nameDict[name]) for name in jsonValidBitNamesWithRealInfo}
    dnsFieldsDict = getDictSubset(dnsFieldsDict, filterValidDNSEntries)

    # dnsFieldDictNS = getDictSubset(dnsFieldsDict, lambda fieldDict: "ns" in fieldDict)

    # byValueDict = collections.defaultdict(list)

    # for name in dnsFieldsDict:
    #     byValueDict[json.dumps(latestValueDNSFields(nameDict[name]))].append(nameDict[name])

    # names_to_check = set([byValueDict[value][0] for value in byValueDict])

    # names_to_check = names_to_check | set([nameDict[name] for name in dnsFieldDictNS.keys()])


    # domains_to_check = [domain.domainName() for domain in names_to_check]

    # print(len(names_to_check))

    # ping = Pinger()
    # ping.thread_count = 16
    # ping.hosts = domains_to_check
    # reachable_domains = ping.start()

    # save_object(reachable_domains, "reachable_domains2.dat")

    # reachable_domains = load_object("reachable_domains.dat")

    # unreachable_names = ["d/" + host[:-4] for host in reachable_domains['dead']]
    # reachable_names = ["d/" + host[:-4] for host in reachable_domains['alive']]

    # print ("Unreachable Names")
    # for nameRecord in unreachable_names:
    #     print(nameRecord.name(), nameRecord.latestValue())

    # print ("\n\nReachable Names")
    # for nameRecord in reachable_names:
    #     print(nameRecord.name(), nameRecord.latestValue())

    recordsToCurl = [nameDict[name] for name in dnsFieldsDict]

    # Remove already curled records
    nameList = set()
    for dirpath, dirnames, filenames in os.walk("front_pages3"):
        for filename in [f for f in filenames if f.endswith("html")]:
            nameList.add('d/' + filename[:-9])

    recordsToCurl = [record for record in recordsToCurl if record.name() not in nameList]

    errorsDict = {"HTTPError" : [], "URLError" : [], "TimeoutError" : [], "socket.timeout" : [], "BadStatusLine" : [], "CertificateError" : [], "Redirection" : [], "ConnectionError" : [], "Other" : []}

    for records in chunks(recordsToCurl, 200):
        result = queue.Queue()
        threads = [threading.Thread(target=downloadDomain, args = (record.domainName(),result)) for record in records]

        for t in threads:
            t.start()
        for t in threads:
            t.join()

        for res in queue_to_list(result):
            if res[1] in errorsDict:
                errorsDict[res[1]].append((res[0], res[2]))
            else:
                folder = "front_pages3/" + json.dumps(latestValueDNSFields(nameDict["d/" + res[0][:-4]])).replace("/", ":")
                if not os.path.exists(folder):
                    os.makedirs(folder)
                with open(folder + "/" + res[0] + ".html", "wb") as text_file:
                    text_file.write(res[2])


    for errorType, dataList in errorsDict.items():
        print("\n\n\n\n", errorType)
        for datum in dataList:
            print(datum)

    # for record in recordsToCurl:
    #     folder = "front_pages3/" + json.dumps(latestValueDNSFields(record)).replace("/", "\/")
    #     downloadDomain(record.domainName(), folder, errorsDict)

    save_object(errorsDict, "curlErrors.dat")
        

    # print("total domains", len(dnsFieldsDict))
    # print("domains to curl", len(domainsToCurl))
    # print(reachable_domains['alive'])
    # save_object(reachable_domains, "reachable_domains.dat")

def chunks(l, n):
    """ Yield successive n-sized chunks from l.
    """
    for i in range(0, len(l), n):
        yield l[i:i+n]

def queue_to_list(q):
    l = []
    while q.qsize() > 0:
        l.append(q.get())
    return l

def downloadDomain(domainName, queue):
    try:
        opened = urlopen('http://' + domainName)
    except HTTPError as e:
        queue.put((domainName, "HTTPError", str(e)))
    except URLError as e:
        queue.put((domainName, "URLError", str(e)))
    except TimeoutError as e:
        queue.put((domainName, "TimeoutError", str(e)))
    except socket.timeout as e:
        queue.put((domainName, "socket.timeout", str(e)))
    except http.client.BadStatusLine as e:
        queue.put((domainName, "BadStatusLine", str(e)))
    except ssl.CertificateError as e:
        queue.put((domainName, "CertificateError", str(e)))
    except ConnectionError as e:
        queue.put((domainName, "ConnectionError", str(e)))
    except Exception as e:
        queue.put((domainName, "Other", str(e)))
    else:
        if not domainName in opened.geturl():
            queue.put((domainName, "Redirection", opened.geturl()))
        else:
            queue.put((domainName, "Valid", opened.read()))


    # if not os.path.exists(folder):
    #         os.makedirs(folder)
    # with open(folder + "/" + domainName + ".html", "wb") as text_file:
    #     text_file.write(page)

def jsonDictAnalysis(nameDict):
    maxHeight = getMaxHeight(nameDict)
    validNames = getDictSubset(nameDict, lambda record: record.isValidAtHeight(maxHeight))
    validBitNames = getDictSubset(validNames, lambda record: record.namespace() == "d")
    jsonValidBitNames = getDictSubset(validBitNames, lambda record: record.latestValueJsonDict())
    jsonValidBitNamesWithRealInfo = getDictSubset(jsonValidBitNames, latestValueDNSFields)

    jsonValidBitNamesOnlyMap = getDictSubset(jsonValidBitNamesWithRealInfo, lambda record: "map" in record.latestValueJsonDict() and "ip" not in record.latestValueJsonDict() and "ns" not in record.latestValueJsonDict())

    dnsFieldsDict = {name:latestValueDNSFields(nameDict[name]) for name in jsonValidBitNamesWithRealInfo}
    dnsFieldsDict = getDictSubset(dnsFieldsDict, filterValidDNSEntries)

    for val in [record.latestValue() for name,record in jsonValidBitNamesOnlyMap.items()]:
        print(val)

    return


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
    # validBitNames = getDictSubset(validNames, lambda record: record.namespace() == "d" and all(x.islower() or x == "_" or x.isdigit() for x in record.name()[2:]) and record.name()[2:] and record.name()[2].islower() and (record.name()[-1].islower() or record.name()[-1].isdigit())
    queries = [
    lambda record: record.isValidAtHeight(maxHeight),
    lambda record: record.namespace() == "d" and all(x.islower() or x == "_" or x.isdigit() for x in record.name()[2:]) and record.name()[2:] and record.name()[2].islower() and (record.name()[-1].islower() or record.name()[-1].isdigit()),
    lambda record: record.latestValueJsonDict(),
    lambda record: latestValueDNSFields(record, nameDict)
    ]

    subsets = [nameDict]
    for i, query in enumerate(queries):
         subsets.append(getDictSubset(subsets[i], query))

    allCounts = [getCounts(subset, NameRecord.latestValue) for subset in subsets]

    # uniqueValidBitValues = getDictSubset(validBitJsonCountsWithRealInfo, lambda x: x <= 10)    
    # counts = getCounts(jsonValidBitNamesWithRealInfo, latestValueServerDNS)

    labels = ["total names", "total valid", "total valid bit", "total valid bit json dict", "total valid bit json with real info"]

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

    matchFields = ["info", "email"]

    for i in range(5, 30):
        possibleSquatterValues = set([value for (value, count) in list(valuesOverN(counter, i))])
        xData.append(i)
        print(i)
        changeCount = 0
        for name in nameDict:
            for session in nameDict[name].sessions:
                squatter = None
                squatterJson = None
                for op in session.valueChangingOps():
                    if op.value not in ignoreValues:
                        if op.value in possibleSquatterValues:
                            squatter = op.value
                            squatterJson = op.jsonDict()
                        elif squatter:
                            skipValue = False
                            jsonValue = op.jsonDict()
                            if jsonValue and squatterJson:
                                if onlyUsedTop(jsonValue) == onlyUsedTop(squatterJson):
                                    skipValue = True
                                for field in matchFields:
                                    if field in jsonValue and field in squatterJson and jsonValue[field] == squatterJson[field]:
                                        skipValue = True
                            if not skipValue:
                                changeCount += 1
                                squatter = None
                            else:
                                squatter = op.value
                            
        yData.append(changeCount)

    
    plt.xlabel(r"\textbf{Squatter Treshold}")
    plt.ylabel(r"\textbf{Number of Transactions}")
    rc('font', serif='Helvetica Neue') 
    rc('text', usetex='true') 
    rcParams.update({'font.size': 16})
    rcParams.update({'figure.autolayout': True})

    ax = plt.subplot(111)
    ax.set_xlim([0,30])
    ax.set_ylim([0,265])
    ax.plot(xData, yData)

    plt.savefig("squatters.eps")

def findSquatterPurchases(nameDict, threshold):

    allValues = [x.value for name in nameDict for session in nameDict[name].sessions for x in session.valueChangingOps()]
    counter = collections.Counter(allValues)

    # print(counter['{"email":"virtcoin@gmail.com"}'])
    # print(counter['{"ip": "74.125.39.104", "info": { "status": "for sale" }, "map": {"": "74.125.39.104", "www": "74.125.39.104"}}'])
    # print(counter['{"ip":"1.2.3.4","email":"mailmeifyouwanttobuythisname@mail.ru","info":"Send an offer to: mailmeifyouwanttobuythisname@mail.ru"}'])
    # print(counter['{"ip":"127.0.0.1","map":{"*":{"ip":"127.0.0.1"}}}'])
    # return

    ignoreValues = set(["", "{}", "{\"ns\":[]}"])

    possibleSquatterValues = set([value for (value, count) in list(valuesOverN(counter, threshold))])

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
    ax.hist(counts, bins=200)
    # ax.hist(counts, bins = 10 ** np.linspace(0, np.log10(60000), 50))
    # ax.semilogx()
    # for axis in [ax.xaxis, ax.yaxis]:
        # axis.set_major_formatter(ScalarFormatter())

def valueOccurenceGraph(nameDict, height):
    valueOps = [nameDict[name].opAtHeight(height) for name in nameDict]
    values = [x.value for x in valueOps if x is not None]
    counter = collections.Counter(values)
    prevCount = 0
    total = 0
    xData = []
    yData = []

    for value, count in reversed(counter.most_common()):
        if count > prevCount:
            xData.append(prevCount)
            yData.append(total)
            for i in range(prevCount + 1, count):
                xData.append(i)
                yData.append(total)
        total += count
        prevCount = count
    xData.append(count)
    yData.append(total)
    fig = plt.figure()
    ax = fig.add_subplot(111)
    plt.plot(xData, yData)
    ax.set_xlabel("At least n occurences")
    ax.set_ylabel("Number of names")
    plt.xscale('log')
    plt.show()

def valueOccurenceGraphInverse(nameDict, height):
    valueOps = [nameDict[name].opAtHeight(height) for name in nameDict]
    values = [x.value for x in valueOps if x is not None]
    counter = collections.Counter(values)
    prevCount = 0
    maxValues = len(values)
    total = len(values)
    xData = []
    yData = []

    for value, count in reversed(counter.most_common()):
        if count > prevCount:
            xData.append(prevCount)
            yData.append(total/maxValues)
            for i in range(prevCount + 1, count):
                xData.append(i)
                yData.append(total/maxValues)
        total -= count
        prevCount = count
    xData.append(count)
    yData.append(total)
    
    ax = plt.subplot(111)
    plt.plot(xData, yData)
    ax.set_xlim([-300,20000])
    formatter = FuncFormatter(to_percent)
    plt.gca().yaxis.set_major_formatter(formatter)


    plt.xlabel(r"\textbf{Value occurs more than n times}")
    plt.ylabel(r"\textbf{Percent of total names}")
    rc('font', serif='Helvetica Neue') 
    rc('text', usetex='true') 
    rcParams.update({'font.size': 16})
    rcParams.update({'figure.autolayout': True})

    # plt.savefig("transfers.eps")

def to_percent(y, position):
    # Ignore the passed in position. This has the effect of scaling the default
    # tick locations.
    s = str(int(100 * y))

    # The percent symbol needs escaping in latex
    if matplotlib.rcParams['text.usetex'] == True:
        return s + r'$\%$'
    else:
        return s + '%'
        

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


    maxHeight = getMaxHeight(nameDict)
    nameDict = {name:nameDict[name] for name in nameDict if nameDict[name].opAtHeight(maxHeight) and nameDict[name].opAtHeight(maxHeight).value}
    valueOccurenceGraphInverse(nameDict, maxHeight)
    plt.show()

    # blockTime = blockTimeDict()
    # alexaAnalysis(nameDict, blockTime)

    # for i in [1000, 10000, 25000, 50000, 100000, 125000, 150000, 175000, 200000, getMaxHeight(nameDict)]:
    #     valueOccurrenceHist(nameDict, i) 
    #     plt.savefig("test/occurenceHist2_" + str(i) + ".png")
    #     plt.clf()

    # rankValidDNSDict(nameDict)

    # currentNameBreakdown(nameDict)

    # resurrectedAnalysis(nameDict)
    # nonResurrectedAnalysis(nameDict)

    # findSquatterPurchases(nameDict)
    # cProfile.run('valueOccurenceTime(nameDict)')

    # findSquatterThreshold(nameDict)

    # bitValueFrequencyAnalysis(nameDict)

    # valueOccurenceTime(nameDict)

    # oneNameAnalysis(nameDict)

    # print(len(getDictSubset(nameDict, lambda record: record.namespace() == "d")))
    # jsonDictAnalysis(nameDict)
    # getRedirects()

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
