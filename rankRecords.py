#!/usr/bin/env python3

import pickle
from nameHistory import getMaxHeight, latestValueDNSFields
from common import getDictSubset

def rankByFunc(nameDict, nameRecordValue, higherIsBetter):
    nameRawValues = {name:nameRecordValue(nameDict[name]) for name in nameDict}

    nameRanks = {}

    rank = 1

    prevUpdates = None

    for (name, value) in sorted(nameRawValues.items(), key=lambda x: x[1], reverse=higherIsBetter):
        if prevUpdates and (value < prevUpdates) is higherIsBetter:
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

def rankNumberOfValueChanges(nameDict, max_height):
    return rankByFunc(nameDict, lambda record: record.numberOfValueChanges(), True)

def rankIsAlive(nameDict, maxHeight):
    return rankByFunc(nameDict, lambda record: int(record.isValidAtHeight(maxHeight)), True)

def rankJSONDict(nameDict, maxHeight):
    rankByFunc(nameDict,
               lambda record: int(record.latestValueJsonDict() is not None),
               True)

def rankValidDNSDict(nameDict, max_height):
    rankByFunc(nameDict,
               lambda record: int(len(latestValueDNSFields(record)) > 0),
               True)

def rankByTimeActive(nameDict, maxHeight):
    return rankByFunc(nameDict,
                      lambda record: record.fractionRegistered(maxHeight),
                      True)


def main():
    with open("nameDict.dat", "rb") as name_file:
        nameDict = pickle.load(name_file)

        bitNames = getDictSubset(nameDict,
                                 lambda record: record.namespace() == "d")
    max_height = getMaxHeight(nameDict)

    valueChangeRank = rankNumberOfValueChanges(nameDict, max_height)
    aliveRank = rankIsAlive(nameDict, max_height)
    validJSONRank = rankJSONDict(nameDict, max_height)
    validDNSRank = rankValidDNSDict(nameDict, max_height)
    timeActiveRank = rankByTimeActive(nameDict, max_height)
    

if __name__ == "__main__":
    main()
