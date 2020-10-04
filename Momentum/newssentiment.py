#!/usr/bin/env python
# coding: utf-8



#### MY PKGS

from nameticker import getTickerName

####

from GoogleNews import GoogleNews
import urllib.request
from bs4 import BeautifulSoup
import nltk
from nltk.sentiment.vader import SentimentIntensityAnalyzer
import requests
import numpy as np
import multiprocessing
import time
import datetime
import numpy as np
import matplotlib.pyplot as plt
import csv
import os
import json



class NewsSentiment(object):
    
    def __init__(self, word, days, synonyms=None):
        self.agent = {"User-Agent":'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Ubuntu Chromium/83.0.4103.61 Chrome/83.0.4103.61 Safari/537.36'}
        if synonyms != None:
            self.synonyms = synonyms.split(',')
        else:
            self.synonyms = [self.getNameFromTicker(word)]
        self.word = word
        self.start, self.end = self.dayMinusDays(days)


    def getNameFromTicker(self,ticker):
        dic = {}
        with open('./ticker-dict.json','r') as JSON:
            dic = json.load(JSON)
    
        if ticker.upper() not in dic.keys():
            getTickerName([ticker.upper()])
            with open('./ticker-dict.json','r') as JSON:
                dic = json.load(JSON)
            return dic[ticker.upper()]
        else:
            return dic[ticker.upper()]
    
    
    def getHtml(self, url, body):
        page = requests.get(url, headers=self.agent)
        if page.text != None:
            body += [page.text]
        else:
            body += ['']
            
            
    def genAllText(self, body, allWords):
        allText = []
        for bod in body:
            soup = BeautifulSoup(bod)
            paragraphs = soup.findAll('p')
            tmpText = ''
            for txt in paragraphs:
                for syn in allWords:
                    if syn.lower() in str(txt).lower():
                        tmpText += txt.getText()
            tmpText = tmpText.replace('\n',' ')
            allText += [tmpText]
        return allText

    
    def genBody(self, links):
        manager = multiprocessing.Manager()
        body = manager.list()
        for url in links:
            print(url)
            p = multiprocessing.Process(target=self.getHtml, args=(url, body,))
            p.start()
            p.join(4)
            if p.is_alive():
                print("timed out...")
                p.terminate()
                p.join()
                body += ['']
            else:
                print('Requests success!')
        return body

    
    ################### NOT IN USE ######################
    def genBodyHeadless(self, links):
        chrome_options = Options()
        chrome_options.add_argument('--headless')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("window-size=1920,1080")
        driver = webdriver.Chrome(ChromeDriverManager().install(),options=chrome_options)
        HTMLs = []
        for url in links:
            driver.get(url)
            HTMLs += [str(driver.page_source.encode("utf-8"))]
        driver.quit()
        return HTMLs
    #####################################################
    
    
    def measureSentiment(self, allText):
        sia = SentimentIntensityAnalyzer()
        pos = 0
        neg = 0
        neu = 0
        com = 0
        count = 0
        print(f'Groups: {len(allText)}')
        for group in allText:
            count += 1
            sentiment = sia.polarity_scores(group)
            pos += sentiment['pos']
            neg += sentiment['neg']
            neu += sentiment['neu']
            com += sentiment['compound']
            print(f'done-{count}')
        return pos,neg,neu,com,count

    
    def avSentiment(self, pos, neg, neu, com, count):
        return pos/count, neg/count, neu/count, com/count
    
    
    def dayMinusDays(self, days):
        timestamp = time.time()
        dateBefore = datetime.datetime.fromtimestamp(timestamp-(days*24*60*60))
        dateNow = datetime.datetime.fromtimestamp(timestamp)
        b = str(dateBefore).split(' ')[0].replace('-','/')
        before = b[5:7]+'/'+b[8:10]+'/'+b[0:4]
        n = str(dateNow).split(' ')[0].replace('-','/')
        now = n[5:7]+'/'+n[8:10]+'/'+n[0:4]
        print(f'Start: {before}')
        print(f'End: {now}')
        return before,now
    
    
    def genCalList(self, start, end):
        MONTHS = [31,28,31,30,31,30,31,31,30,31,30,31]
        start_d = int(start[3:5])
        start_m = int(start[0:2])
        end_d = int(end[3:5])
        end_m = int(end[0:2])
        year = int(end[6:])
        month_dif = end_m - start_m
        day_dif = end_d - start_d
        calList = []
        
        if month_dif == 0:
            for d in range(start_d,end_d+1):
                date = str(year)+'/'+self.formatDay(start_m)+'/'+self.formatDay(d)
                calList += [date]
            return calList

        for m in range(month_dif+1):
            if m == 0:
                for d in range(start_d, MONTHS[start_m-1]+1):
                    date = self.formatDay(start_m)+'/'+self.formatDay(d)+'/'+str(year)
                    calList += [date]
            elif m == month_dif:
                for d in range(1,end_d+1):
                    date = self.formatDay(end_m)+'/'+self.formatDay(d)+'/'+str(year)
                    calList += [date]
            else:
                for d in range(1,MONTHS[start_m+m-1]+1):
                    date = self.formatDay(start_m+m)+'/'+self.formatDay(d)+'/'+str(year)
                    calList += [date]                    
        return calList
    
    
    def formatDay(self, day):
        if int(day) < 10:
            return f'0{day}'
        return str(day)
    
    
    def extrapolate(self, array):
        indices = [i for i, x in enumerate(array) if x == 0]
        av = sum(array)/(len(array)-len(indices))
        for ind in indices:
            array[ind] = av
        return array
    
    
    def getSentimentFromJson(self, jsonPath):
        with open(jsonPath, 'r') as JSON:
            data = json.load(JSON)
        dates = [i for i in data.keys()]
        calList = self.genCalList(dates[0],dates[-1])
        pos,neg,neu,com = [],[],[],[]
        samples = 0
        missing = 0
        for date in calList:
            try:
                pos += [data[date]['pos']]
                neg += [data[date]['neg']]
                neu += [data[date]['neu']]
                com += [data[date]['com']]
                samples += data[date]['sample size']
            except:
                pos += [0.0]
                neg += [0.0]
                neu += [0.0]
                com += [0.0]
                missing += 1
        print(f'Missing: {missing}')
        print(f'Total: {len(calList)}\n')
        return pos,neg,neu,com,samples
    
            
    def genTrend(self, days, data, path):
        x = [i for i in range(len(data[-days:]))]
        y = [i for i in self.extrapolate(data[-days:])]
        z = np.polyfit(x, y, 1)
        p = np.poly1d(z)
        ext = f"trend-{days}.npy"
        with open(path+ext,'wb') as f:
            np.save(f, np.array(p(x)))
            
    
    def getComData(self):
        path = f'./news/data/{self.word}/'
        pos,neg,neu,com,samples = self.getSentimentFromJson(path+f'{self.word}.json')
        com = self.extrapolate(com)
        return com
        
    
    def trend(self):
        path = f'./news/data/{self.word}/'
        pos,neg,neu,com,samples = self.getSentimentFromJson(path+f'{self.word}.json')
        days = [180,90,30,10,3]
        comL = self.extrapolate(com)
        for day in days:
            if len(comL) >= day:
                self.genTrend(day,comL,path)
                print(f'{day} success!')
            else:
                print(f'{day} not enough data...')
                
    
    def getSlope(self,data):
        first = data[0]
        last = data[-1]
        slope = (last-first)/len(data)
        return slope
    
    
    def slope(self):
        self.trend()
        formatted = {}
        days = [3,10,30,90,180]
        for day in days:
            path = f'./news/data/{self.word}/trend-{day}.npy'
            data = np.load(path)
            slope = self.getSlope(data)
            formatted[str(day)] = slope
        with open(f'./news/data/{self.word}/slopes.json','w') as JSON:
            json.dump(formatted,JSON)
            
    
    def run(self):
        googlenews = GoogleNews()
        calList = self.genCalList(self.start,self.end)
        posL,negL,neuL,comL = [],[],[],[]

        pageCount = 10
        ALL_RESULT = {}
        t = time.time()

        for date in calList:
            print(f'\n\n{date}')
            PREV_RES = []
            RESULT = {}
            continu = True

            for page in range(1,pageCount+1):
                t1 = time.time()
                googlenews = GoogleNews(start=date, end=date, lang='en')
                googlenews.search(self.word)
                googlenews.getpage(page)
                results = googlenews.result()
                googlenews.clear()
                
                if results == []:
                    continu = False
                    break

                results = [dict(t) for t in {tuple(d.items()) for d in results}]
                results = [i for i in results if i not in PREV_RES]
                if len(results) < 1:
                    break

                for res in results:
                    RESULT[res['title']] = res['link']
                                        
                PREV_RES = results
                print(f"Page: {page}. Name: {self.word}. t={round(time.time()-t1,2)}s")

            if not os.path.exists(f'./news/data/{self.word}'):
                os.mkdir(f'./news/data/{self.word}')

            old_data = {}
            if os.path.isfile(f'./news/data/{self.word}/{self.word}.json'):
                with open(f'./news/data/{self.word}/{self.word}.json','r') as JSON:
                    old_data = json.load(JSON)
                    JSON.close()

            if continu == False:
                print('No results.')
                with open(f'./news/data/{self.word}/{self.word}.json','w') as JSON:
                    old_data[date] = {}
                    json.dump(old_data,JSON)
                    JSON.close()
                continue

            titles = [i for i in RESULT.keys()]
            links = [i for i in RESULT.values()]
            body = self.genBody(links)
            allWords = [self.word] + self.synonyms

            print('\nFetching <p> text...')
            oldText = self.genAllText(body,allWords)
            allText = [i for i in oldText if i != '']
            print(f"Texts aquired of total: {(len(allText)/len(oldText))*100}%")

            if allText == []:
                with open(f'./news/data/{self.word}/{self.word}.json','w') as JSON:
                    old_data[date] = {}
                    json.dump(old_data,JSON)
                    JSON.close()
                continue

            print('Sentiment analysis...')
            pos,neg,neu,com,count = self.measureSentiment(allText)
            pos_,neg_,neu_,com_ = self.avSentiment(pos,neg,neu,com,count)

            posL += [pos_]
            negL += [neg_]
            neuL += [neu_]
            comL += [com_]

            formatted = {'synonyms':self.synonyms,'pos':pos_,'neg':neg_,'neu':neu_,'com':com_,'raw text':allText,'sample size':len(RESULT),'page count':pageCount}
            old_data[date] = formatted
            with open(f'./news/data/{self.word}/{self.word}.json','w') as JSON:
                json.dump(old_data,JSON)
                JSON.close()

        print(time.time()-t)



#word = 'gt gold corp'
#days = 15
#n = NewsSentiment(word,days,synonyms='gt gold')

#n.run()






