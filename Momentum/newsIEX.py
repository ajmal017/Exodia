#!/usr/bin/env python
# coding: utf-8


import pyEX as p

import json
import os
import datetime
import time
import requests

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager

from googletrans import Translator

import nltk
from nltk.sentiment.vader import SentimentIntensityAnalyzer
from bs4 import BeautifulSoup


class NewsIEX(object):
    
    def __init__(self):
        self.secret = 'sk_fae174660924464996b77d14209a973b'
        self.public = 'pk_2f3691af11ad4df583c95f2a4d89d44a'
        p.Client(api_token=self.secret, version='v1', api_limit=5)
        self.chrome_options = Options()
        self.chrome_options.add_argument("--headless")
        self.agent = {"User-Agent":'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Ubuntu Chromium/83.0.4103.61 Chrome/83.0.4103.61 Safari/537.36'}

    
    def genCalList(self,days):
        base = datetime.datetime.today()
        date_list = [str(i).split(' ')[0] for i in [base - datetime.timedelta(days=x) for x in range(days)]]
        return date_list
    
    
    def prepNews(self,ticker):
        daysAgo = 30
        sent_data = {}
        SENT_PATH = f'./news/sentiment/{ticker}.json'      

        if os.path.exists(SENT_PATH):
            with open(SENT_PATH,'r') as JSON:
                sent_data = json.load(JSON)
        
        with open('./ticker-dict.json') as JSON:
            tickers = json.load(JSON)
            subName = tickers[ticker]

        sia = SentimentIntensityAnalyzer()
        translator = Translator()
        
        if str(sent_data).count('{') < 5:
            print(f'Less than {daysAgo} news articles.')
            news = p.news(count=(daysAgo), symbol=ticker, token=self.secret, version='v1')
            
            cc = 0
            print(f'News LENGTH: {len(news)}')
            for story in news:
                timestamp = story['datetime']
                date = str(datetime.datetime.fromtimestamp(int(str(timestamp)[0:-3]))).split(' ')[0]
                print(date)
                url = story['url']
                summary = story['summary']
                lang = story['lang']
                hasPaywall = story['hasPaywall']
                
                if lang != 'en':
                    try:
                        summary = translator.translate(summary).text
                    except:
                        summary = ''
                
                if hasPaywall != True:       
                    HTML = requests.get(url,headers=self.agent).text
                    soup = BeautifulSoup(HTML,features="lxml")
                    paragraphs = soup.findAll('p')

                    allText = []
                    for peice in paragraphs:
                        if ticker.lower() in str(peice).lower() or subName.lower().split(' ')[0] in str(peice).lower():
                            txt = str(peice.getText())
                            if lang != 'en':
                                peice = translator.translate(txt).text
                            allText += [txt]

                    TEXT = ' '.join(allText)
                    if TEXT == '':
                        print('No text... using summary')
                        TEXT = summary
                    sentiment = sia.polarity_scores(TEXT)
                    
                else:
                    sentiment = sia.polarity_scores(summary)

                formatted = {
                        'url':url,
                        'summary':summary,
                        'lang':lang,
                        'hasPaywall':hasPaywall,
                        'sentiment':sentiment,
                    }

                try:
                    sent_data[date] = sent_data[date] + [formatted]
                except:
                    sent_data[date] = [formatted]
                cc += 1
                print(f'{cc} done.')
                #sentimentSummary = sia.polarity_scores(summary)
        
            last = int(str(news[-1]['datetime'])[0:-3])
            first = time.time() #int(str(news[-1]['datetime'])[0:-3])
            delta = first-last
            DAYS = int(delta/60/60/24)

            print(f'Delta: {DAYS}')
            date_list = self.genCalList(DAYS)

            KEYS = sent_data.keys()
            for dt in date_list:
                if dt not in KEYS:
                    sent_data[dt] = {}

            try:
                sent_data['lastDeltaAv'] = (sent_data['lastDeltaAv'] + DAYS)/2
            except:
                sent_data['lastDeltaAv'] = DAYS
            

            with open(SENT_PATH,'w') as JSON:
                json.dump(sent_data,JSON)
        
 
                
    def getNews(self,ticker):
        self.prepNews(ticker)
        sent_data = {}
        SENT_PATH = f'./news/sentiment/{ticker}.json'
        
        
        if os.path.exists(SENT_PATH):
            with open(SENT_PATH,'r') as JSON:
                sent_data = json.load(JSON)

        with open('./ticker-dict.json') as JSON:
            tickers = json.load(JSON)
            subName = tickers[ticker]
        
        sia = SentimentIntensityAnalyzer()
        translator = Translator()

        firstLastDelta = sent_data['lastDeltaAv'] + 1
        newsDays = (10)//firstLastDelta + 1
        news = p.news(count=newsDays, symbol=ticker, token=self.secret, version='v1')

        for story in news:
            timestamp = story['datetime']
            date = str(datetime.datetime.fromtimestamp(int(str(timestamp)[0:-3]))).split(' ')[0]
            url = story['url']
            summary = story['summary']
            lang = story['lang']
            hasPaywall = story['hasPaywall']

            
            if lang != 'en':
                try:
                    summary = translator.translate(summary).text
                except:
                    summary = ''
            
            if hasPaywall != True:
                HTML = requests.get(url,headers=self.agent).text
                soup = BeautifulSoup(HTML,features="lxml")
                paragraphs = soup.findAll('p')

                allText = []
                for peice in paragraphs:
                    if ticker.lower() in str(peice).lower() or subName.lower().split(' ')[0] in str(peice).lower():
                        txt = str(peice.getText())
                        if lang != 'en':
                            peice = translator.translate(txt).text
                        allText += [txt]

                TEXT = ' '.join(allText)
                if TEXT == '':
                    print('No text... using summary')
                    TEXT = summary
                sentiment = sia.polarity_scores(TEXT)
            else:
                sentiment = sia.polarity_scores(summary)

            formatted = {
                    'url':url,
                    'summary':summary,
                    'lang':lang,
                    'hasPaywall':hasPaywall,
                    'sentiment':sentiment,
                }

            try:
                sent_data[date] = sent_data[date] + [formatted]
            except:
                sent_data[date] = [formatted]
            #sentimentSummary = sia.polarity_scores(summary)
                
        
        last = int(str(news[-1]['datetime'])[0:-3])
        first = time.time() #int(str(news[-1]['datetime'])[0:-3])
        delta = first-last
        DAYS = int(delta/60/60/24)
        
        print(f'First last day delta: {DAYS}')
        date_list = self.genCalList(DAYS)
        
        KEYS = sent_data.keys()
        for dt in date_list:
            if dt not in KEYS:
                sent_data[dt] = {}
                
        try:
            sent_data['lastDeltaAv'] = (sent_data['lastDeltaAv'] + DAYS)/2
        except:
            sent_data['lastDeltaAv'] = DAYS

        with open(SENT_PATH,'w') as JSON:
            json.dump(sent_data,JSON)

        print(f'Done {newsDays} days.')




#n = NewsIEX()
#n.getNews('HEXO',1)




