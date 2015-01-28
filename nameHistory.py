#!/usr/bin/env python

import sys
import logging
import matplotlib.pyplot as plt
import datetime
import os.path
import json

execfile("common.py")

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

def getCounts(nameDict, nameListFunc):
    bucketList = {}
    for name in nameDict:
        bucket = nameListFunc(nameDict[name])
        if bucket in bucketList:
            bucketList[bucket] += 1
        else:
            bucketList[bucket] = 1
    return bucketList

def main(argv):

    nameDict = {}
    nameNewDict = {}

    if not os.path.isfile("nameDict.dat"):
        a = datetime.datetime.now()
        dataList = load_object("python_raw.dat")
        b = datetime.datetime.now()
        c = b - a
        print c.total_seconds()
        print "Finished loading data"

        for nameInfo in dataList:
            if nameInfo.tx_type() == "new":
                nameNewDict[nameInfo.tx_hash] = nameInfo

        print "Found", len(nameNewDict), "new names"

        for nameInfo in dataList:
            if nameInfo.tx_type() == "firstUpdate":
                tx_hash = hash160(nameInfo.tx_rand + nameInfo.name)
                if tx_hash in nameNewDict:
                    if nameInfo.name in nameDict:
                        nameDict[nameInfo.name].append(nameNewDict[tx_hash])
                        nameDict[nameInfo.name].append(nameInfo)
                    else:
                        nameDict[nameInfo.name] = [nameNewDict[tx_hash], nameInfo]
                    del nameNewDict[tx_hash]
                

            if nameInfo.tx_type() == "update":
                if nameInfo.name in nameDict:
                    nameDict[nameInfo.name].append(nameInfo)
                else:
                    nameDict[nameInfo.name] = [nameInfo]
            # print nameInfo.height, nameInfo.tx_type, nameInfo.name

        print len(nameNewDict), "unused NameNew transactions"

        save_object(nameDict, "nameDict.dat")
        save_object(nameNewDict.values(), "unusedNameNew.dat")
    else:
        nameDict = load_object("nameDict.dat")
        # nameNewDict = load_object("unusedNameNew.dat")

    updateCount = getCounts(nameDict, getNumberOfNameTransactions)
    changeUpdateCount = getCounts(nameDict, getNumberOfValueChanges)
    ownerChangeCount = getCounts(nameDict, getNumberOfOwnerChanges)

    print "Name Transactions"
    for length in updateCount:
        print length, updateCount[length]

    print "Value Changes"
    for length in changeUpdateCount:
        print length, changeUpdateCount[length]

    print "Owner Changes"
    for length in ownerChangeCount:
        print length, ownerChangeCount[length]
    
if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))