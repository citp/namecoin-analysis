#!/usr/bin/env python3
import collections
import matplotlib.pyplot as plt
import tldextract
import re
from IPy import IP
from common import *

def isPrivateIP(ipAddressString, filterSquatters):
    squatterIps = ["144.76.12.6", "5.35.253.206", "212.232.51.96", "99.192.226.225", "178.63.142.162", "178.63.16.21"]
    try:
        if filterSquatters and ipAddressString in squatterIps:
            return True
        ipAddress = IP(ipAddressString)
        ipType = ipAddress.iptype()
        return ipType == "PRIVATE" or ipType == "LOOPBACK"
    except:
        return False

def isValidIp(ip):
    allowed = re.compile("([0-9]{1,3}\.){3}[0-9]{1,3}")
    return allowed.match(ip)

def isValidNS(hostname, filterSquatters):
    squatterNS = ["ns1.domaincoin.net", "ns2.domaincoin.net", "ns1.khezri.ir", "ns2.khezri.ir", "ns0.web-sweet-web.net", "ns1.web-sweet-web.net"]
    if filterSquatters and hostname in squatterNS:
        return False
    else:
        return is_valid_hostname(hostname)

def validDNSFields(record, filterSquatters):
    serverFields = ["service", "ip", "ip6", "tor", "ip2", "freenet", "alias", "translate", "ns", "delegate", "import", "map"]
    dataFields = ["email", "loc", "info", "fingerprint", "tls", "ds"]
    json_object = record.jsonDict()
    if json_object:
        serverKeys = [key for key in list(set(json_object.keys()) & set(serverFields)) if len(json_object[key]) > 0]
        dnsOnlyObject = {key:json_object[key] for key in json_object if key in serverKeys}
        return filterValidDNSEntries(dnsOnlyObject, filterSquatters)
    else:
        return None

def filterValidDNSEntries(json_object, filterSquatters):
    serverFields = ["service", "ip", "ip6", "tor", "ip2", "freenet", "alias", "translate", "ns", "delegate", "import", "map"]
    fieldDict = {key: json_object[key] for key in json_object if key in serverFields}

    if "map" in fieldDict:
        if isinstance(fieldDict["map"], dict):
            subdomains = list(fieldDict["map"].keys())
            for subdomain in subdomains:
                if isinstance(fieldDict["map"][subdomain], str):
                    if isPrivateIP(fieldDict["map"][subdomain], filterSquatters):
                        del fieldDict["map"][subdomain]
                elif isinstance(fieldDict["map"][subdomain], dict):
                    fieldDict["map"][subdomain] = filterValidDNSEntries(fieldDict["map"][subdomain], filterSquatters)
                    if not fieldDict["map"][subdomain]:
                        del fieldDict["map"][subdomain]
            if not fieldDict["map"]:
                del fieldDict["map"]
        else:
            del fieldDict["map"]

    if "ip" in fieldDict:
        if isinstance(fieldDict["ip"], str):
            if isPrivateIP(fieldDict["ip"], filterSquatters):
                del fieldDict["ip"]
        elif isinstance(fieldDict["ip"], list):
            fieldDict["ip"] = [ip for ip in fieldDict["ip"] if not isPrivateIP(ip, filterSquatters)]
            if not fieldDict["ip"]:
                del fieldDict["ip"]
        else:
            del fieldDict["ip"]

    if "ns" in fieldDict:
        if isinstance(fieldDict["ns"], list):
            fieldDict["ns"] = [ns for ns in fieldDict["ns"] if isValidIp(ns) or isValidNS(ns, filterSquatters)]
            if not fieldDict["ns"]:
                del fieldDict["ns"]
        else:
            del fieldDict["ns"]

    if "translate" in fieldDict:
        if isinstance(fieldDict["translate"], str):
            if fieldDict["translate"].startswith("BM-") or "Bitmessage adress" in fieldDict["translate"] or "@" in fieldDict["translate"]:
                del fieldDict["translate"]

    return fieldDict

def get_expiration_depth(height):
    if height < 24000:
        return 12000
    if height < 48000:
        return height - 12000
    return 36000

def trackNamesOverTime(dataList, blockTime, tracFunc, graphPercentage):
    recordsByHeight = collections.defaultdict(list)
    lastHeight = 0
    for nameInfo in [x for x in dataList if x.hasValue()]:
        recordsByHeight[nameInfo.height].append(nameInfo)

    xData = []
    yData = []
    trackedActiveNameDict = {}
    allActiveNames = {}
    expiration_dict = collections.OrderedDict()
    for height in sorted(recordsByHeight):
        expiration_depth = get_expiration_depth(height) + height
        while expiration_dict and next(iter(expiration_dict)) < height:
            expiryHeight, expiryList = expiration_dict.popitem(last=False)
            for name in expiryList:
                del allActiveNames[name]
                trackedActiveNameDict.pop(name, None)
        # trackedRecords = tracFunc(recordsByHeight[height])
        trackedRecords = [record for record in recordsByHeight[height] if tracFunc(record)]
        otherRecords = [record for record in recordsByHeight[height] if record not in trackedRecords and record.name in trackedActiveNameDict]
        if expiration_depth not in expiration_dict:
            expiration_dict[expiration_depth] = []
        for record in recordsByHeight[height]:
            if record.name in allActiveNames:
                expiration_dict[allActiveNames[record.name]].remove(record.name)
            allActiveNames[record.name] = expiration_depth
            expiration_dict[expiration_depth].append(record.name)
        for record in trackedRecords:
            trackedActiveNameDict[record.name] = expiration_depth
        for record in otherRecords:
            del trackedActiveNameDict[record.name]
        xData.append(blockTime[height])
        if graphPercentage:
            yData.append(float(len(trackedActiveNameDict))/(float(len(allActiveNames))))
        else:
            yData.append(len(trackedActiveNameDict))
    return xData, yData

def topValueSplitGraph(dataList, blockTime, buckets):

    valueList = [op.value for op in dataList if op.hasValue()]
    counter = collections.Counter(valueList)
    del counter[""]

    for index, occurences in enumerate(buckets): 
        topVals = set(valuesOverN(counter, occurences))
        values = {value for (value, count) in topVals}

        xData, yData = trackNamesOverTime(dataList, blockTime, lambda record: record.value in values)
        plt.subplot(111)
        if not index:
            label = "Greater than " + str(occurences) + " occurences"
        else:
            label = "Between " + str(buckets[index - 1]) + " and " + str(occurences) + " occurences"
        plt.plot(xData, yData, label=label)

        for value in values:
            del counter[value]

    remainingValues = set([value for (value, count) in counter.most_common()])
    xData, yData = trackNamesOverTime(dataList, blockTime, lambda record: record.value in remainingValues)
    plt.plot(xData, yData, label="Fewer than " + str(buckets[-1]) + " occurences")

    plt.legend(loc='upper left')

def nameLength(dataList, blockTime):
    xData, yData = trackNamesOverTime(dataList, blockTime, lambda record: record.name.startswith("d/") and len(record.nameWithoutNamespace()) <= 3, True)
    plt.subplot(111)
    plt.plot(xData, yData, label="1-3")

    xData, yData = trackNamesOverTime(dataList, blockTime, lambda record: record.name.startswith("d/") and 4 <= len(record.nameWithoutNamespace()) <= 6, True)
    plt.subplot(111)
    plt.plot(xData, yData, label="4-6")

    xData, yData = trackNamesOverTime(dataList, blockTime, lambda record: record.name.startswith("d/") and 7 <= len(record.nameWithoutNamespace()) <= 14, True)
    plt.subplot(111)
    plt.plot(xData, yData, label="7-14")

    xData, yData = trackNamesOverTime(dataList, blockTime, lambda record: record.name.startswith("d/") and 15 <= len(record.nameWithoutNamespace()) <= 20, True)
    plt.subplot(111)
    plt.plot(xData, yData, label="15-20")

    xData, yData = trackNamesOverTime(dataList, blockTime, lambda record: record.name.startswith("d/") and len(record.nameWithoutNamespace()) >= 21, True)
    plt.subplot(111)
    plt.plot(xData, yData, label="Over 21")

    plt.legend(loc='upper left')

def dictionaryNames(dataList, blockTime):
    words = set([word.strip() for word in open('/usr/share/dict/words', 'r')])
    xData, yData = trackNamesOverTime(dataList, blockTime, lambda record: record.name.startswith("d/") and record.nameWithoutNamespace() in words, True)
    plt.plot(xData, yData)

def dirtyNames(dataList, blockTime):
    words = [word.strip() for word in open('dirty.txt', 'r')]
    words = set([word for word in words if " " not in word])
    xData, yData = trackNamesOverTime(dataList, blockTime, lambda record: record.name.startswith("d/") and any(word in record.name.lower() for word in words), False)
    plt.plot(xData, yData)

def namespaceCounts(dataList):
    namespaceList = []
    updateList = [x for x in dataList if x.hasValue()]
    for record in updateList:
        splitName = record.name.split('/')
        if len(splitName) > 1:
            namespaceList.append(splitName[0])
    return collections.Counter(namespaceList)

def validLookingDotBit(dataList, blockTime):
    xData, yData = trackNamesOverTime(dataList, blockTime, lambda record: record.name.startswith("d/") and validDNSFields(record, False), True)
    plt.subplot(111)
    plt.plot(xData, yData, label="Working DNS with squatter")

    xData, yData = trackNamesOverTime(dataList, blockTime, lambda record: record.name.startswith("d/") and validDNSFields(record, True), True)
    plt.subplot(111)
    plt.plot(xData, yData, label="Working DNS without squatter")

    # xData, yData = trackNamesOverTime(dataList, blockTime, lambda record: record.name.startswith("d/"))
    # plt.subplot(111)
    # plt.plot(xData, yData, label="All")
    plt.legend(loc='upper left')

def namespaceGraph(dataList, blockTime):
    counts = namespaceCounts(dataList)
    for (value, count) in counts.most_common(10):
        xData, yData = trackNamesOverTime(dataList, blockTime, lambda record: record.name.startswith(value + "/"))
        plt.subplot(111)
        plt.plot(xData, yData, label="active in namespace " + value)
    plt.legend(loc='upper left')
    plt.show()

def alexaGraph(dataList, blockTime):
    dotBitAlexa = alexaRanks()
    # xData, yData = trackNamesOverTime(dataList, blockTime, lambda record: record.name.lower() in dotBitAlexa, True)
    # plt.plot(xData, yData)

    groups = [10000, 100000, 250000, 500000, 1000000]
    for i in groups:
        alexa_names = set([key for key, value in dotBitAlexa.items() if value <= i])
        xData, yData = trackNamesOverTime(dataList, blockTime, lambda record: record.name in alexa_names, True)
        plt.plot(xData, yData, label="top " + str(i) + " domains")
    plt.legend(loc='upper left')




blockTime = blockTimeDict()
dataList = load_object("python_raw.dat")
alexaGraph(dataList, blockTime)
# namespaceGraph(dataList, blockTime)
# validLookingDotBit(dataList, blockTime)
# nameLength(dataList, blockTime)
# dictionaryNames(dataList, blockTime)
# dirtyNames(dataList, blockTime)
# topValueSplitGraph(dataList, blockTime, [10000, 500, 5])
plt.show()
# for i in [10, 25, 50, 100, 250, 500, 1000, 2500, 5000, 10000]:
#   topValueSplitGraph(i, dataList, blockTime)
#   plt.savefig("test/over" + str(i) + "split.png")
#   plt.clf()
