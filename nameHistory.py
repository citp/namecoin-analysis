#!/usr/bin/env python3

import sys
import logging
import matplotlib.pyplot as plt
import datetime
import os.path
import json
<<<<<<< HEAD
import operator
import collections
import csv
import tldextract
from IPy import IP
import re

from common import NameNew, NameUpdate, NameFirstUpdate, load_object, save_object, hash160

def getNumberOfNameTransactions(opList):
    return len(opList)

def getNumberOfValueChanges(opList):
    changeUpdates = 0
    lastValue = ""
    for op in opList:
        if op.tx_type() == "firstUpdate":
            lastValue = op.value
        elif op.tx_type() == "update":
            if op.value != lastValue:
                changeUpdates += 1
            lastValue = op.value
    return changeUpdates

def getNumberOfOwnerChanges(opList):
    ownerChanges = 0
    lastOwner = ""
    for op in opList:
        if op.tx_type() != "new":
            if op.to_pub_id == lastOwner:
                ownerChanges += 1
        lastOwner = op.to_pub_id
    return ownerChanges

def getLatestValue(opList):
    return opList[-1].value

def getNamespace(opList):
   return opList[-1].name.split('/')[0] 

def getCounts(nameDict, nameListFunc):
<<<<<<< HEAD
    bucketList = collections.defaultdict(int)
    for name in nameDict:
        bucketList[nameListFunc(nameDict[name])] += 1
    return bucketList

def currentValueList(nameDict):
    return [record[-1].value for record in nameDict]

def nameHasPrefix(prefix):
    def checkPrefix(opList):
        return opList[-1].name.startswith(prefix)
    return checkPrefix

def nameIsValid(opList):
    currentBlockNum = 208455
    return opList[-1].height > currentBlockNum - 36000

def latestValueIsJson(opList):
    myjson = opList[-1].value
    try:
        json_object = json.loads(myjson)
    except ValueError:
        return False
    return True

def is_valid_hostname(hostname):
    if len(hostname) > 255:
        return False
    if hostname[-1:] == ".":
        hostname = hostname[:-1]
    allowed = re.compile("(?!-)[A-Z\d-]{1,63}(?<!-)$", re.IGNORECASE)
    return all(allowed.match(x) for x in hostname.split("."))

def isValidIp(ip):
    allowed = re.compile("([0-9]{1,3}\.){3}[0-9]{1,3}")
    return allowed.match(ip)

def latestValueIsValidDNS(opList):
    serverFields = ["service", "ip", "ip6", "tor", "ip2", "freenet", "alias", "translate", "ns", "delegate", "import", "map"]
    dataFields = ["email", "loc", "info", "fingerprint", "tls", "ds"]
    myjson = opList[-1].value
    try:
        json_object = json.loads(myjson)
        if not isinstance(json_object, dict):
            return False

        serverKeys = [key for key in list(set(json_object.keys()) & set(serverFields)) if len(json_object[key]) > 0]
        if "translate" in serverKeys:
            if isinstance(json_object["translate"], str):
                if not is_valid_hostname(json_object["translate"]):
                    serverKeys.remove("translate")
                if json_object["translate"].startswith("BM-"):
                    serverKeys.remove("translate")
        if "ns" in serverKeys:
            if not isinstance(json_object["ns"], list):
                serverKeys.remove("ns")
            else:
                validList = [ns for ns in json_object["ns"] if isValidIp(ns) or is_valid_hostname(ns)]
                if not validList:
                    serverKeys.remove("ns")

        if not serverKeys:
            return False
        if "map" in json_object:
            if not isinstance(json_object["map"], dict):
                return False
            if "" in json_object["map"]:
                if isinstance(json_object["map"][""], str):
                    if isPrivateIP(json_object["map"][""]):
                        return False
        if "ip" in json_object:
            if isinstance(json_object["ip"], str):
                if isPrivateIP(json_object["ip"]):
                    return False

    except ValueError:
        return False
    return True

def latestValueServerDNS(opList):
    serverFields = ["service", "ip", "ip6", "tor", "ip2", "freenet", "alias", "translate", "ns", "delegate", "import", "map"]
    dataFields = ["email", "loc", "info", "fingerprint", "tls", "ds"]
    myjson = opList[-1].value
    json_object = json.loads(myjson)
    return  [str(key, json_object[key]) for key in list(set(json_object.keys()) & set(serverFields)) if len(json_object[key]) > 0].join(", ")

def isPrivateIP(ipAddressString):
    ipAddress = IP(ipAddressString)
    ipType = ipAddress.iptype()
    return ipType == "PRIVATE" or ipType == "LOOPBACK"
    
def getDictSubset(nameDict, conditionFunc):
    return { key:value for key, value in nameDict.items() if conditionFunc(value) }

def getTopValues(valueCounts, threshold):
    for w in sorted(valueCounts, key=valueCounts.get, reverse=True):
        yield w, valueCounts[w]
        if valueCounts[w] < threshold:
            break

def getAggregateValues(valueCounts):
    squatterEmails = ["nmc.name.for.sale@gmail.com", "namecoin.domains@gmail.com", "Virtcoin@gmail.com", "info2014@cassini.tv",
                     "mybitname@gmail.com", "But234s@yandex.com", "info2015@cassini.tv", "bitdomainsell@gmail.com", "virtcoin@gmail.com",
                     "rent@emojibit.com", "nabil2442@gmail.com", "mybitname@gmail.com", "hupperdehup@gmail.com", "domains.bit@gmail.com",
                     "salenamecoin@gmail.com", "stan14142000@yahoo.ca", "dotbitgod@gmail.com", "yd567@yadex.com", "BitAssets@163.com",
                     "frostpako@centrum.cz", "daniel_r_plante@hotmail.com", "piramatizomai@gmail.com", "mailmeifyouwanttobuythisname@mail.ru",
                     "bitdomains@yandex.com", "18058280610@163.com"]
    valueCountsAggregate = collections.defaultdict(int)
    for value in valueCounts:
        foundAggregate = False
        if "BM-2c" in value:
            valueCountsAggregate["Aggregate-BitMessage"] += valueCounts[value]
            foundAggregate = True
        
        for email in squatterEmails:
            if email in value:
                valueCountsAggregate["Aggregate-Squatter"] += valueCounts[value]
                foundAggregate = True

        if not foundAggregate:
            valueCountsAggregate[value] = valueCounts[value]
    return valueCountsAggregate

def getPurchasesFromRegistrar(nameDict):
    registrarValues = {"dotbit" : 
    ['{ \"info\": { \"registrar\": \"dotbit.me\", \"registrar-email\": \"admin@dotbit.me\" }, \"ip\": \"178.63.16.21 \", \"map\": { \"*\": { \"ip\": \"178.63.16.21\" } } }', 
    '{ \"info\": { \"registrar\": \"dotbit.me\", \"registrar-email\": \"admin@dotbit.me\" }, \"ip\": \"144.76.12.6\", \"map\": { \"*\": { \"ip\": \"144.76.12.6\" } } }'],
    "domaincoin" : ["{\"ns\": [\"ns1.domaincoin.net\", \"ns2.domaincoin.net\"]}"],
    "bitres" : ["{\"ip\":\"83.160.102.54\",\"ip6\":\"2001:980:608c:1:215:5dff:fe00:a301\",\"map\":{\"*\":{\"ip\":\"83.160.102.54\",\"ip6\":\"2001:980:608c:1:215:5dff:fe00:a301\"}},\"website\":\"http://bitres.domyn.com\",\"email\":\"bitres@domyn.com\",\"bitmessage\":\"BM-2cVNwE6TYj23XNjxNw2a3kcCEQYoe3uPg3\",\"namecoin\":\"N3dbLhnUoEEHtGHokRwwfrA92PBJXZvaCP\",\"about\":\"bit domain reservation\"}"],
    "bitzinc" : ["{\"info\":\"Want this domain? Contact dotbit@bitzinc.com\",\"ip\":\"92.222.26.81\",\"ip6\":\"2001:41d0:52:a00:0:0:0:a16\",\"map\":{\"www\":{\"ip\":\"92.222.26.81\",\"ip6\":\"2001:41d0:52:a00:0:0:0:a16\"}}}"],
    "dot-bit" : ["{\"info\":{\"registrar\":\"http://register.dot-bit.org\"},\"ns\":[\"ns0.web-sweet-web.net\",\"ns1.web-sweet-web.net\"],\"map\":{\"\":{\"ns\":[\"ns0.web-sweet-web.net\",\"ns1.web-sweet-web.net\"]}}}"],
    "jay_dee" : ["\"ns\":[\"If you are interested in this domain please contact Jay Dee at namecoin.domains@gmail.com for more details.\"]}"],
    "bitassets" : ["{info:make an offer if you intrest,email:BitAssets@163.com}"],
    "daniel_r" : ["{\"info\": {\"email\": \"daniel_r_plante@hotmail.com\"} }"],
    "devin" : ["{\"name\":\"Devin\",\"email\":\"newporthighlander@gmail.com\"}"],
    "virtcoin" : ["Contact Virtcoin@gmail.com if interested in purchasing."],
    "cex" : ["{\"info\": \"mybitname@gmail.com see more here http://goo.gl/B5y1em\"}"],
    "nmcreg" : ["{\"email\":\"nmc.reg@gmail.com\",\"description\":\"name for sale\"}"],
    "hupperdehup" : ["{\"email\":\"hupperdehup@gmail.com\",\"bitmessage\":\"This domain is for sale.\"}"]
    }

    registrarTotalCounts = {}
    registrarCurrentCounts = {}
    for registrar in registrarValues:
        registrarTotalCounts[registrar] = 0
        registrarCurrentCounts[registrar] = 0

    for name in nameDict:
        owner = ""
        for tx in nameDict[name]:
            if tx.tx_type() != "new":
                foundRegistrar = False
                for registrar in registrarValues:
                    if tx.value in registrarValues[registrar]:
                        if owner != registrar:
                            registrarTotalCounts[registrar] += 1
                            if owner != "":
                                ()
                                # print name, "changed registrar from", owner, "to", registrar
                        owner = registrar
                        foundRegistrar = True
                if not foundRegistrar and owner != "":
                    # print name, "changed ownership from", owner, "to", tx.value
                    owner = ""
        if owner != "":
            registrarCurrentCounts[owner] += 1
    print("Registrar Current Counts")
    for registrar in registrarCurrentCounts:
        print(registrar, registrarCurrentCounts[registrar])
    print("Registrar Total Counts")
    for registrar in registrarTotalCounts:
        print(registrar, registrarTotalCounts[registrar])

def bitValueFrequencyAnalysis(nameDict):

    validNames = getDictSubset(nameDict, nameIsValid)
    validBitNames = getDictSubset(validNames, nameHasPrefix("d/"))
    jsonValidBitNames = getDictSubset(validBitNames, latestValueIsJson)
    nonJsonValidBitNames = getDictSubset(validBitNames, lambda x: not latestValueIsJson(x))
    jsonValidBitNamesWithRealInfo = getDictSubset(jsonValidBitNames, latestValueIsValidDNS)
    jsonValidBitNamesWithBadInfo = getDictSubset(jsonValidBitNames, lambda x: not latestValueIsValidDNS(x))



    valueCounts = getCounts(nameDict, getLatestValue)
    validValueCounts = getCounts(validNames, getLatestValue)
    validBitValueCounts = getCounts(validBitNames, getLatestValue)
    validBitJsonCounts = getCounts(jsonValidBitNames, getLatestValue)
    validBitNonJsonCounts = getCounts(nonJsonValidBitNames, getLatestValue)
    validBitJsonCountsWithRealInfo = getCounts(jsonValidBitNamesWithRealInfo, getLatestValue)
    validBitJsonCountsWithBadInfo = getCounts(jsonValidBitNamesWithBadInfo, getLatestValue)
    uniqueValidBitValues = getDictSubset(validBitJsonCountsWithRealInfo, lambda x: x <= 10)
    
    counts = getCounts(jsonValidBitNamesWithRealInfo, latestValueServerDNS)


    print("unique valid bit", len(uniqueValidBitValues))
    print("total names:", len(nameDict), "unique", len(valueCounts))
    print("total valid:", len(validNames), "unique", len(validValueCounts))
    print("total valid bit", len(validBitNames), "unique", len(validBitValueCounts))
    print("total valid bit not json", len(nonJsonValidBitNames), "unique", len(validBitNonJsonCounts))
    print("total valid bit json", len(jsonValidBitNames), "unique", len(validBitJsonCounts))
    print("total valid bit json with real info", len(jsonValidBitNamesWithRealInfo), "unique", len(validBitJsonCountsWithRealInfo))
    print("total valid bit json with bad info", len(jsonValidBitNamesWithBadInfo), "unique", len(validBitJsonCountsWithBadInfo))
    print("test", len(counts))

    print("\nTop non json values")

    for value in counts:
        print(counts[value], value)
    # for value, count in getTopValues(validBitNonJsonCounts, 20):
    #     print(count, value)

    # print("\n\nTop good json values")

    # for value, count in getTopValues(validBitJsonCountsWithRealInfo, 20):
    #     print(count, value)

    # print("\n\nTop bad json values")

    # for value, count in getTopValues(validBitJsonCountsWithBadInfo, 20):
    #     print(count, value)

    # print("\n\Rare good json values")

    # for value in uniqueValidBitValues:
    #     print(value)

def oneNameAnalysis(nameDict):
    oneName = getDictSubset(nameDict, nameHasPrefix("u/"))
    validOneName = getDictSubset(oneName, nameIsValid)
    nonReserved = getDictSubset(validOneName, lambda x: "reservations@onename.io" not in getLatestValue(x))
    counts = getCounts(nonReserved, getLatestValue)
    uniqueValues = getDictSubset(counts, lambda x: x == 1)

    print("total u records:", len(oneName))
    print("valid u records:", len(validOneName))
    print("non reserved records", len(nonReserved))
    print("unique non reserved records", len(uniqueValues))

def findSquatterPurchases(nameDict):

    allValues = []
    for name in nameDict:
        isFirst = True
        for record in nameDict[name]:
            if record.tx_type() != "new":
                if (not isFirst and prevVal != record.value) or isFirst:
                    allValues.append(record.value)
                    prevVal = record.value

    counter = collections.Counter(allValues)

    # print(counter.most_common(120))

    ignoreValues = ["", "{\"map\": {\"\": \"10.0.0.1\"}}", "{\"map\": {\"\": \"127.0.0.1\"}}", "{\"map\":{\"\":\"127.0.0.1\"}}"]
    possibleSquatterValues = [value for (value, count) in counter.most_common(400)]

    changesDict = collections.defaultdict(list)
    changesList = []

    interestingUpdateDict = {}
    for name in nameDict:
        owner = ""
        interestingUpdates = []
        for tx in nameDict[name]:
            if tx.tx_type() != "new":
                if tx.value not in ignoreValues:
                    foundRegistrar = False
                    if tx.value in possibleSquatterValues or "guy@guydresher" in tx.value:
                        foundRegistrar = True
                        if tx.value != "":
                            owner = tx.value
                    if not foundRegistrar and owner != "":
                        # print(name, "changed ownership from", owner, "to", tx.value)
                        changesList.append((owner, tx.value))
                        changesDict[(owner, tx.value)].append(name)
                        owner = ""
            else:
                owner = ""

    uniqueChanges = [(changesDict[change][0], change) for change in changesDict if len(changesDict[change]) == 1]

    for (name, value) in uniqueChanges:
        print(name, value)



def main(argv):

    nameDict = {}
    nameNewDict = {}

    if not os.path.isfile("nameDict.dat"):
        a = datetime.datetime.now()
        dataList = load_object("python_raw.dat")
        b = datetime.datetime.now()
        c = b - a
        print(c.total_seconds())
        print("Finished loading data")

        for nameInfo in dataList:
            if nameInfo.tx_type() == "new":
                nameNewDict[nameInfo.tx_hash] = nameInfo

        print("Found", len(nameNewDict), "new names")

        for nameInfo in dataList:
            if nameInfo.tx_type() == "firstUpdate":
                if nameInfo.tx_hash in nameNewDict:
                    if nameInfo.name in nameDict:
                        nameDict[nameInfo.name].append(nameNewDict[nameInfo.tx_hash])
                        nameDict[nameInfo.name].append(nameInfo)
                    else:
                        nameDict[nameInfo.name] = [nameNewDict[nameInfo.tx_hash], nameInfo]
                    del nameNewDict[nameInfo.tx_hash]
                

            if nameInfo.tx_type() == "update":
                if nameInfo.name in nameDict:
                    nameDict[nameInfo.name].append(nameInfo)
                else:
                    nameDict[nameInfo.name] = [nameInfo]
            # print nameInfo.height, nameInfo.tx_type, nameInfo.name

        print(len(nameNewDict), "unused NameNew transactions")

        save_object(nameDict, "nameDict.dat")
        # save_object(nameNewDict.values(), "unusedNameNew.dat")
    else:
        nameDict = load_object("nameDict.dat")
        # nameNewDict = load_object("unusedNameNew.dat")

    # namesInAlexa = {}
    # failedDomains = []
    # with open('top-1m.csv', 'rb') as csvfile:
    #     reader = csv.reader(csvfile)
    #     for row in reader:
    #         rank = row[0]
    #         url = row[1]
    #         try:
    #             parsed_url = tldextract.extract(url)
    #             bitDomain = "d/" + parsed_url.domain
    #             if bitDomain in nameDict:
    #                 namesInAlexa[bitDomain] = nameDict[bitDomain]
    #         except UnicodeError, e:
    #             failedDomains.append(url)

    # print "Found", len(namesInAlexa), "bit domains"
    # print "failed domains", failedDomains



    # findSquatterPurchases(getDictSubset(nameDict, nameHasPrefix("d/")))

    # valueFrequencyAnalysis(nameDict)

    # validNames = getDictSubset(nameDict, nameIsValid)
    # valueCountsByNamespace = getCounts(validNames, lambda x : "Namespace " + getNamespace(x) + ": " + getLatestValue(x))
    # namespaceCount = getCounts(validNames, getNamespace)

    # for value, count in getTopValues(namespaceCount, 20):
    #     print(count, value)

    # for value, count in getTopValues(valueCountsByNamespace, 50):
    #     print(count, value)

    bitValueFrequencyAnalysis(nameDict)
    # oneNameAnalysis(nameDict)

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
