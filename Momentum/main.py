#!/usr/bin/env python
# coding: utf-8

# In[111]:


from stockSnapshot import Stock
from commentssentiment import CommentSentiment
from commentEMA import GenerateEMA
from newsIEX import NewsIEX
from nameticker import getTickerName

# In[114]:


import schedule
import time
import datetime
import json

# In[125]:

print('Starting...')

def function(tickerList):
    now = str(datetime.datetime.now())
    nowDate = now.split(' ')[0]
    nowMin = now.split(' ')[1]
    
    n = NewsIEX()
    for tick in tickerList:
        n.getNews(tick)
    
    while int(nowMin[0:2]) < 16:
        for tim in range(6):
            print(f'Done {tim}. Time: {nowMin}')
            for tick in tickerList:
                #2.0 seconds for new stocks 
                Stock(tick).run()
            time.sleep(5*60-(0.3*len(tickerList)))
                
        for tick in tickerList:
            cs = CommentSentiment(tick,'newest')
            cs.saveStocktwits()
            cs.saveYahoo()
            
        now = str(datetime.datetime.now())
        nowDate = now.split(' ')[0]
        nowMin = now.split(' ')[1]
        
    print('\n\nDONE FOR THE DAY :)')
    schedule.every().day.at("09:30").do(run,tickerList)
    print('Waiting till tomorrow morning...')
    while True:
        schedule.run_pending()
        time.sleep(60)

        
def run(tickerList):
    now = str(datetime.datetime.now())
    nowDate = now.split(' ')[0]
    nowMin = now.split(' ')[1]
    
    with open('./ticker-dict.json','r') as JSON:
        tickerNames = json.load(JSON)
    
    unnamed = [i for i in tickerList if i not in tickerNames.keys()]
    if len(unnamed) > 0:
        getTickerName(unnamed)

    print(nowMin[0:2])
    if int(nowMin[0:2]) < 10 and int(nowMin[3:5]) < 30:
        schedule.every().day.at("09:30").do(function,tickerList)
        print('Waiting till tomorrow morning...')
        while True:
            schedule.run_pending()
            time.sleep(60)
    elif int(nowMin[0:2]) > 16:
        schedule.every().day.at("09:30").do(function,tickerList)
        print('Waiting till tomorrow morning...')
        while True:
            schedule.run_pending()
            time.sleep(60)
    else:
        function(tickerList)
        
        

    #cs.parseStocktwitsComments('HEXO')
    #cs.parseYahooComments('HEXO')
    
    #ema = GenerateEMA()
    #ema.genEMA('HEXO',15,'yahoo')
    
    #AdjData = ema.getEMAdata('HEXO',15,'yahoo','adj')


# In[126]:


txt = open('tickers.txt','r').read().replace('\n','')
tickerList = txt.split(',')
print(tickerList)
run(tickerList)

