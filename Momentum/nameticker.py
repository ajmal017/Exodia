#!/usr/bin/env python
# coding: utf-8

from bs4 import BeautifulSoup
import json
import re
import requests
import json
import time
import datetime
import os


def getTickerName(tickerList):
    tickerNames = []
    for tic in tickerList:
        Stocktwits_URL = f'https://api.stocktwits.com/api/2/streams/symbol/{tic}.json?filter=top'
        HTML = requests.get(Stocktwits_URL)
        data = HTML.json()
        
        name = data['symbol']['title']
        name = name.replace(',','')
        name = name.replace('.','')
#         name = name.replace('Inc','')
#         name = name.replace('Ltd','')
#         name = name.replace('Corp','')
        name = name.replace('  ',' ')
        
        if name[-1] == ' ':
            name = name[0:-1]
        tickerNames += [name]
        
    complete = {tickerList[i]:tickerNames[i] for i in range(len(tickerList))}
    
    old_data = {}
    if os.path.isfile('./ticker-dict.json'):
        with open('ticker-dict.json','r') as JSON:
            old_data = json.load(JSON)
            JSON.close()
    
    for dic in complete:
        old_data[dic] = complete[dic]
    
    with open('ticker-dict.json','w') as JSON:
        json.dump(old_data,JSON)
        JSON.close()





