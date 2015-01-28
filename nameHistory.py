#!/usr/bin/env python

import sys
import logging
import matplotlib.pyplot as plt
import datetime
import os.path
import json

execfile("common.py")

def getNumberOfChangeUpdates(opList):
    changeUpdates = 0
    lastValue = ""
    for op in opList:
        if op.tx_type() == "new":
            changeUpdates = 0
        elif op.tx_type() == "firstUpdate":
            lastValue = op.value
        elif op.tx_type() == "update":
            if op.value != lastValue:
                changeUpdates += 1
                lastValue = op.value
    return changeUpdates



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

    updateCount = {}
    changeUpdateCount = {}

    for name in nameDict:
        length = len(nameDict[name])
        changeUpdates = getNumberOfChangeUpdates(nameDict[name])

        if length in updateCount:
            updateCount[length] += 1
        else:
            updateCount[length] = 1

        if changeUpdates > 8:
            print name

        if changeUpdates in changeUpdateCount:
            changeUpdateCount[changeUpdates] += 1
        else:
            changeUpdateCount[changeUpdates] = 1

    print "Updates"
    for length in updateCount:
        print length, updateCount[length]

    print "Change Updates"
    for length in changeUpdateCount:
        print length, changeUpdateCount[length]

    
if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))