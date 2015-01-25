#!/usr/bin/env python

import sys
import logging
import matplotlib.pyplot as plt
import datetime

execfile("common.py")

def main(argv):
    a = datetime.datetime.now()
    dataList = load_object("python_raw.dat")
    b = datetime.datetime.now()
    c = b - a
    print c.total_seconds()
    print "Finished loading data"
    
    nameDict = {}

    for nameInfo in dataList:
        if nameInfo.tx_type > 0:
            if nameInfo.name in nameDict:
                nameDict[nameInfo.name].append(nameInfo)
            else:
                nameDict[nameInfo.name] = [nameInfo]
        # print nameInfo.height, nameInfo.tx_type, nameInfo.name

    save_object(nameDict, "nameDict.dat")

    
if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))