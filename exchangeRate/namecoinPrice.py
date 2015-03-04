#!/usr/bin/env python3
import json
import matplotlib.pyplot as plt
import datetime
import collections
import numpy

json_bitcoin_data = open('bitcoin.json')
json_namecoin_data=open('namecoin.json')
namecoin_data = json.load(json_namecoin_data)
bitcoin_data = json.load(json_bitcoin_data)
json_bitcoin_data.close()
json_namecoin_data.close()

print(bitcoin_data.keys())

xData = []
yData = []
bitcoinValueDict = {}
for dataPoint in namecoin_data["price_usd_data"]:
	date = dataPoint[0]/1000
	btcValue = dataPoint[1]
	bitcoinValueDict[date] = btcValue
	xData.append(datetime.datetime.fromtimestamp(date))
	yData.append(btcValue)
	
plt.plot(xData, yData)
plt.show()
		
# bitcoinAverageValue = {date:numpy.mean(bitcoinValueDict[date]) for date in bitcoinValueDict}

# for exchange in bitcoin_data:
# 	xData = []
# 	yData = []
# 	for dataPoint in exchange["ExchangeSnapshots"]:
# 		date = dataPoint[0]/1000
# 		btcValue = dataPoint[1]
# 		xData.append(datetime.datetime.fromtimestamp(date))
# 		yData.append(btcValue)
# 	plt.plot(xData, yData, label=exchange["Exchange"])
# 	plt.legend()
# plt.show()


# for exchange in namecoin_data:
# 	xData = []
# 	yData = []
# 	for dataPoint in exchange["ExchangeSnapshots"]:
# 		date = dataPoint[0]/1000
# 		btcValue = dataPoint[1]
# 		xData.append(datetime.datetime.fromtimestamp(date))
# 		bitcoinValue = bitcoinAverageValue.get(date) or bitcoinAverageValue[min(bitcoinAverageValue.keys(), key=lambda k: abs(k-date))]
# 		yData.append(bitcoinValue * btcValue)
# 	plt.plot(xData, yData, label=exchange["Exchange"])
# 	plt.legend()
# plt.show()