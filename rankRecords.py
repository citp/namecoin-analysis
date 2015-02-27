#!/usr/bin/env python3

import pickle
from nameHistory import getMaxHeight, latestValueDNSFields
from common import getDictSubset, alexaRanks
from csv import DictReader
from nltk.corpus import wordnet

from sklearn.linear_model import ElasticNet

from sklearn.metrics import roc_auc_score as AUC
from sklearn.cross_validation import train_test_split

from segment_string import SegmentString


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
    return nameRanks

def rankNumberOfValueChanges(nameDict, max_height):
    return rankByFunc(nameDict, lambda record: record.numberOfValueChanges(), True)

def rankIsAlive(nameDict, maxHeight):
    return rankByFunc(nameDict, lambda record: int(record.isValidAtHeight(maxHeight)), True)

def rankJSONDict(nameDict, maxHeight):
    return rankByFunc(nameDict,
               lambda record: int(record.latestValueJsonDict() is not None),
               True)

def rankValidDNSDict(nameDict, max_height):
    return rankByFunc(nameDict,
               lambda record: int(len(latestValueDNSFields(record)) > 0),
               True)

def rankByTimeActive(nameDict, maxHeight):
    return rankByFunc(nameDict,
                      lambda record: record.fractionRegistered(maxHeight),
                      True)

def price(ranks, maxRank):
    totalPrice = 0
    for rank in ranks:
        totalPrice += ((maxRank - rank) / maxRank)
    return totalPrice

def main():
    with open("nameDict.dat", "rb") as name_file:
        nameDict = pickle.load(name_file)

        bitNames = getDictSubset(nameDict,
                                 lambda record: record.namespace() == "d")
    max_height = getMaxHeight(nameDict)

    dotBitAlexa = alexaRanks()
    dirtyWords = [word.strip() for word in open('dirty.txt', 'r') if " " not in word]
    dictWords = set([word.strip() for word in open('/usr/share/dict/words', 'r')])
    bitWordList = set(["coin", "satoshi", "wallet", "crypto", "currency", "btc", "nmc", "blockchain"])
    with open("name_lists/surnames.csv", "r") as surnames_file:
        reader = DictReader(surnames_file)
        surnamesSet = set(line["name"].lower() for line in reader)

    valueChangeRank = rankNumberOfValueChanges(bitNames, max_height)
    aliveRank = rankIsAlive(bitNames, max_height)
    validJSONRank = rankJSONDict(bitNames, max_height)
    validDNSRank = rankValidDNSDict(bitNames, max_height)
    timeActiveRank = rankByTimeActive(bitNames, max_height)

    maxRank = len(bitNames)
    xData = []
    yData = []
    for name in bitNames:
        yData.append(price([valueChangeRank[name], aliveRank[name], validJSONRank[name], validDNSRank[name], timeActiveRank[name]], maxRank))
        xData.append([
            int(dotBitAlexa[name]) + 1,                                                       # alexaRank
            int(len(wordnet.synsets(name[2:])) >= 1) + 1,                                       # inDict
            int(any(dirtyWord in name.lower() for dirtyWord in dirtyWords)) + 1,                # inDirty
            int(set(name[2:]).issubset(set("0123456789"))) + 1,                                 # isNumber
            len(name),                                                                          # length
            int(any(word in name.lower() for word in bitWordList) or name.startswith("d/bit")) + 1, # coinRelated
            int(set(name[2:]).issubset(set("abcdefghijklmnopqrstuvwxyz"))) + 1,
            SegmentString().string_segments(name[2:])
    ])

    x_train, x_test, y_train, y_test = train_test_split(xData, yData, test_size=.10, random_state=33)

    alpha = 0.1
    enet = ElasticNet(alpha=alpha)
    y_pred_enet = enet.fit(x_train, y_train).score(x_test, y_test)   
    print(y_pred_enet)
    print(enet.get_params())

if __name__ == "__main__":
    main()
