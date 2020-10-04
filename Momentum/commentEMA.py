#!/usr/bin/env python
# coding: utf-8


# t=today
# y=yesterday
# N=number of days in EMA
# k=2÷(N+1)
# EMA=Price(t)×k+EMA(y)×(1−k)



import time
import datetime
import json
import random
import os
import matplotlib.pyplot as plt



class GenerateEMA(object):
    
    def __init__(self):
        pass
    

    def formatDay(self,day):
        if int(day) < 10:
            return f'0{day}'
        return str(day)
    
    
    def genTimeStamps(self,start,end):
        start_hour = int(start[0:2])
        start_min = int(start[3:5])
        end_hour = int(end[0:2])
        end_min = int(end[3:5])

        timestampList = []
        for hour in range(start_hour,end_hour+1):
            timestampList += [self.formatDay(hour)+':'+'00']
            timestampList += [self.formatDay(hour)+':'+'30']
        return timestampList
    

    def generateRandomData(self,ticker,days,ST_YAHOO):
        base = datetime.datetime.today()
        calList = [str(i).split(' ')[0] for i in [base - datetime.timedelta(days=x) for x in range(days)]]

        try:
            with open(f'./comments/p/{ST_YAHOO}/{ticker}.json','r') as JSON:
                data = json.load(JSON)
                JSON.close()
        except:
            data = {}

        timestamps = self.genTimeStamps('08:00','20:00')
        for DATE in calList:
            for t in timestamps:
                try:
                    f = data[DATE]
                except:
                    f = {}
                f[t] = {}
                try:
                    d = data[DATE][t]['average_sentiment']
                except:
                    f[t]['average_sentiment'] = random.uniform(-1.0, 1.0)
                try:
                    d = data[DATE][t]['adjusted_sentiment']
                except:
                    f[t]['adjusted_sentiment'] = random.uniform(-1.0, 1.0)
                try:
                    d = data[DATE][t]['first_last_delta']
                except:
                    f[t]['first_last_delta'] = random.uniform(0,200)

                data[DATE] = f

        with open(f'./comments/p/{ST_YAHOO}/{ticker}.json','w') as JSON:
            json.dump(data,JSON)
            JSON.close()

        print('Done.')
        
        
        
    def genEMA(self,ticker,days,ST_YAHOO):
        base = datetime.datetime.today()
        calList = [str(i).split(' ')[0] for i in [base - datetime.timedelta(days=x) for x in range(days)]]

        dataEMA = {}
        if os.path.isfile(f'./comments/ema/{ST_YAHOO}/{ticker}_{days}.json'):
            with open(f'./comments/ema/{ST_YAHOO}/{ticker}_{days}.json','r') as JSON:
                dataEMA = json.load(JSON)
                JSON.close()

        try:
            with open(f'./comments/p/{ST_YAHOO}/{ticker}.json','r') as JSON:
                data = json.load(JSON)
                JSON.close()
        except:
            print("This stock doesn't have any data yet.")
            return

        N = days
        k = 2/(N+1)
        timestamps = self.genTimeStamps('08:00','20:00')
        total = 0
        missing = 0
        for num in range(len(calList)):
            formatted = {}
            if num == 0:
                for t in timestamps:
                    formatted[t] = {}
                    try:
                        formatted[t]['av'] = data[calList[num]][t]['average_sentiment']
                        formatted[t]['adj'] = data[calList[num]][t]['adjusted_sentiment']
                        formatted[t]['vol'] = data[calList[num]][t]['first_last_delta']
                        total += 1
                    except:
                        missing += 1
                        
                dataEMA[calList[num]] = formatted
                continue

            for t in timestamps:
                formatted[t] = {}
                try:
                    todayAv = data[calList[num]][t]['average_sentiment']
                    yesterdayAvEMA = dataEMA[calList[num-1]][t]['av']
                    AvEMA = (todayAv*k) + (yesterdayAvEMA*(1-k))

                    todayAdj = data[calList[num]][t]['adjusted_sentiment']
                    yesterdayAdjEMA = dataEMA[calList[num-1]][t]['adj']
                    AdjEMA = (todayAdj*k) + (yesterdayAdjEMA*(1-k))

                    todayVol = data[calList[num]][t]['first_last_delta']
                    yesterdayVolEMA = dataEMA[calList[num-1]][t]['vol']
                    VolEMA = (todayVol*k) + (yesterdayVolEMA*(1-k))

                    formatted[t]['av'] = AvEMA
                    formatted[t]['adj'] = AdjEMA
                    formatted[t]['vol'] = VolEMA

                    total += 1
                except:
                    missing += 1
                dataEMA[calList[num]] = formatted
                
        with open(f'./comments/ema/{ST_YAHOO}/{ticker}_{days}.json','w') as JSON:
            json.dump(dataEMA,JSON)
            JSON.close()

        print('Done.')
        print(f'Total: {total}')
        print(f'Missing: {missing}')
        
        
        
    def getEMAdata(self,ticker,days,ST_YAHOO,AV_ADJ_VOL):        
        try:
            with open(f'./comments/ema/{ST_YAHOO}/{ticker}_{days}.json','r') as JSON:
                data = json.load(JSON)
        except:
            print(f'EMA for {days} does not exist.')
            return

        allData = []
        for DATE in data:
            for timestamp in data[DATE]:
                try:
                    allData += [data[DATE][timestamp][AV_ADJ_VOL]]
                except:
                    allData += [0.0]

        return allData

#ticker = 'TSLA'
#days = 20
#ST_YAHOO = 'stocktwits'

#cc = GenerateEMA()
#AdjData = cc.getEMAdata(ticker,days,ST_YAHOO,'adj')
#cc.genEMA(ticker,days,ST_YAHOO)



##########################################################

#AvData = getEMAdata(tiker,days,ST_YAHOO,'av')
#print('Average sentiment.')
#plt.plot([i for i in range(len(AvData))],AvData)


#AdjData = getEMAdata(tiker,days,ST_YAHOO,'adj')
#print('Adjusted sentiment.')
#plt.plot([i for i in range(len(AdjData))],AdjData)


#VolData = getEMAdata(tiker,days,ST_YAHOO,'vol')
#print('Volume.')
#plt.plot([i for i in range(len(VolData))],VolData)




