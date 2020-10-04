#!/usr/bin/env python
# coding: utf-8


import time
import datetime
import requests
import json
import os
import numpy as np

import nltk
from nltk.sentiment.vader import SentimentIntensityAnalyzer

from textblob import TextBlob
#nltk.download('vader_lexicon')




class CommentSentiment(object):
    def __init__(self, ticker, popularOrNewest):
        self.placeholder = 'placeholder'
        self.popularNewest = popularOrNewest
        self.Stocktwits_URL = f'https://api.stocktwits.com/api/2/streams/symbol/{self.placeholder}.json?filter=top'
        self.Yahoo_URL = f'https://finance.yahoo.com/_finance_doubledown/api/resource/canvass.getMessageListForContext_ns;context=finmb_{self.placeholder};count=30;index=null;lang=en-US;namespace=yahoo_finance;oauthConsumerKey=finance.oauth.client.canvass.prod.consumerKey;oauthConsumerSecret=finance.oauth.client.canvass.prod.consumerSecret&sortBy={self.popularNewest}'
        self.ticker = ticker.upper()
        
    def getYahooIdWithTicker(self):
        agent = {"User-Agent":'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Ubuntu Chromium/83.0.4103.61 Chrome/83.0.4103.61 Safari/537.36'}
        txt = requests.get(f'http://thelion.com/bin/aio_msg.cgi?cmd=search&symbol={self.ticker}&x=0&y=0',headers=agent)
        spli = txt.text.split('<a href="https://finance.yahoo.com/_finance_doubledown/api/resource/canvass.getMessageListForContext_ns;context=finmb_')
        Id = spli[1][:9]
        return Id
        
    def getStocktwitsComments(self):
        agent = {"User-Agent":'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Ubuntu Chromium/83.0.4103.61 Chrome/83.0.4103.61 Safari/537.36'}
        comments = requests.get(self.Stocktwits_URL.replace(self.placeholder,self.ticker),agent)
        return comments.json()
    
    def getYahooComments(self):
        agent = {"User-Agent":'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Ubuntu Chromium/83.0.4103.61 Chrome/83.0.4103.61 Safari/537.36'}
        tickerId = self.getYahooIdWithTicker()
        comments = requests.get(self.Yahoo_URL.replace(self.placeholder,tickerId),agent)
        return comments.json()
    
    def saveStocktwitsComment(self,comments):
        # datas = ['ideas','followers','following','likes/total','replies','watchlist_stocks_count','join_date']
        # 'entities', 'sentiment'
        
        msgFirst = comments['messages'][0]
        msgLast = comments['messages'][-1]
        
        msgFirstTime = time.mktime(datetime.datetime.strptime(msgFirst['created_at'], "%Y-%m-%dT%H:%M:%SZ").timetuple())
        msgLastTime = time.mktime(datetime.datetime.strptime(msgLast['created_at'], "%Y-%m-%dT%H:%M:%SZ").timetuple())
        timeDelta = (msgFirstTime-msgLastTime)/60
        
        old_data = {}
        last_comment = ''
        if os.path.isfile(f'./comments/stocktwits/{self.ticker}.json'):
            with open(f'./comments/stocktwits/{self.ticker}.json','r') as JSON:
                old_data = json.load(JSON)
                last_comment = old_data['last_comment']
                JSON.close()
        
        DATE = str(datetime.datetime.now()).split(' ')[0]
        TIME = str(datetime.datetime.now()).split(' ')[1].split('.')[0]
        
        body = {'first_last_delta':timeDelta,'average_sentiment':0,'adjusted_sentiment':0,'comments':{}}
        totalSentiment = 0
        adjustedSentiment = 0
        sentimentDivider = 0
        cc = 0
        for msg in comments['messages']:
            uID = msg['id']
            uBody = msg['body'] 
            uCreatedAt = msg['created_at']
            uFollowers = int(msg['user']['followers'])
            uFollowing = int(msg['user']['following'])
            uWatchListCount = int(msg['user']['watchlist_stocks_count'])
            uJoinDate = msg['user']['join_date']
             
            try:
                uLikes = int(msg['likes']['total'])
            except:
                uLikes = 0   
            try:
                uReplies = int(msg['conversation']['replies'])
            except:
                uReplies = 0
            try:
                uSentiment = msg['entities']['sentiment']['basic']
            except:
                uSentiment = 'None'


            if uSentiment == 'Bullish':
                uSentimentAnalysis = 1.0
            elif uSentiment == 'Bearish':
                uSentimentAnalysis = -1.0
            else:
                blob = TextBlob(uBody)
                blob.tags
                blob.noun_phrases 
                total = []
                if len(blob.sentences) > 0:
                    for sentence in blob.sentences:
                        print(sentence,sentence.sentiment.polarity)
                        total += [sentence.sentiment.polarity]
                    uSentimentAnalysis = sum(total)/len(total) #sia.polarity_scores(uBody)
                else:
                    uSentimentAnalysis = 0.0

            multiplier = (uLikes/(1+uFollowers))**0.6 * uFollowers
            adjustedSentiment += uSentimentAnalysis + (multiplier*uSentimentAnalysis)
            sentimentDivider += (multiplier + 1)
            totalSentiment += uSentimentAnalysis
            
#             print(f'Sentiment: {uSentimentAnalysis}')
#             print(f'Adj Sentiment: {uSentimentAnalysis + (multiplier*uSentimentAnalysis)}')
#             print(msg['user']['username'])
#             print(f'Followers: {uFollowers}')
            
            formatted = {
                'body':uBody,
                'created_at':uCreatedAt,
                'followers':uFollowers,
                'following':uFollowing,
                'likes':uLikes,
                'watchlist_stocks_count':uWatchListCount,
                'join_date':uJoinDate,
                'replies':uReplies,
                'sentiment':uSentiment,
                'sentiment_analysis':uSentimentAnalysis
            }
            body['comments'][uID] = formatted
            cc += 1
#             print(f'Comment {cc} done.\n')
            
        body['average_sentiment'] = totalSentiment/cc
        body['adjusted_sentiment'] = adjustedSentiment/sentimentDivider
        
        print('\n\n\n')
        print(f'Adj Sentiment: {adjustedSentiment/sentimentDivider}')
        print(f'Sentiment: {totalSentiment/cc}')
        
        old_data['last_comment'] = msgFirst['body']
        if DATE not in old_data.keys():
            old_data[DATE] = {}
            
        old_data[DATE][TIME] = body
        with open(f'./comments/stocktwits/{self.ticker}.json','w') as JSON:
            json.dump(old_data,JSON)
            JSON.close()
    
    def saveYahooComment(self,comments):
        # datas = ['ideas','followers','following','likes/total','replies','watchlist_stocks_count','join_date']
        # 'entities', 'sentiment'
        
        # canvasMessages -> "author" -> "createdAt,details[userText],reactionStats[upVoteCount,downVoteCount,replyCount]
        
        msgFirst = comments['canvassMessages'][0]
        msgLast = comments['canvassMessages'][-1]
        
        msgFirstTime = msgFirst['meta']['createdAt']
#         return msgFirst
        msgLastTime = msgLast['meta']['createdAt']
        timeDelta = (msgFirstTime-msgLastTime)/60
        
        old_data = {}
        last_comment = ''
        if os.path.isfile(f'./comments/yahoo/{self.ticker}.json'):
            with open(f'./comments/yahoo/{self.ticker}.json','r') as JSON:
                old_data = json.load(JSON)
                last_comment = old_data['last_comment']
                JSON.close()
        
        DATE = str(datetime.datetime.now()).split(' ')[0]
        TIME = str(datetime.datetime.now()).split(' ')[1].split('.')[0]
        
        body = {'first_last_delta':timeDelta,'average_sentiment':0,'adjusted_sentiment':0,'comments':{}}
        totalSentiment = 0
        adjustedSentiment = 0
        sentimentDivider = 0
        cc = 0
        for msg in comments['canvassMessages']:
            uID = msg['meta']['author']['guid']
            uBody = msg['details']['userText']
            uCreatedAt = msg['meta']['createdAt']
            uFollowers = 0 #int(msg['user']['followers'])
            uFollowing = 0 #int(msg['user']['following'])
            uWatchListCount = 0 #int(msg['user']['watchlist_stocks_count'])
            uJoinDate = 0 #msg['user']['join_date']
             
            try:
                uLikes = int(msg['reactionStats']['upVoteCount'])
            except:
                uLikes = 0   
            try:
                uDislikes = int(msg['reactionStats']['downVoteCount'])
            except:
                uDislikes = 0   
            try:
                uReplies = int(msg['reactionStats']['replyCount'])
            except:
                uReplies = 0
            try:
                uSentiment = msg['userLabels']
            except:
                uSentiment = 'None'


            if uSentiment == 'Bullish':
                uSentimentAnalysis = 1.0
            elif uSentiment == 'Bearish':
                uSentimentAnalysis = -1.0
            else:
                blob = TextBlob(uBody)
                blob.tags
                blob.noun_phrases 
                total = []
                if len(blob.sentences) > 0: 
                    for sentence in blob.sentences:
                        print(sentence,sentence.sentiment.polarity)
                        total += [sentence.sentiment.polarity]
                    uSentimentAnalysis = sum(total)/len(total) #sia.polarity_scores(uBody)
                else:
                    uSentimentAnalysis = 0.0

            uLikes += 1
            uDislikes += 1 
            
            Total = uLikes + uDislikes
            likeRatio = uLikes/Total
            dislikeRatio = uDislikes/Total
            sentimentSum = Total * ((likeRatio*uSentimentAnalysis) - (dislikeRatio*uSentimentAnalysis))
            adjustedSentiment += uSentimentAnalysis + sentimentSum
            sentimentDivider += (1 + (Total-2))
            totalSentiment += uSentimentAnalysis
            
#             print(f'Sentiment: {adjustedSentiment}')
#             print(msg['meta']['author']['nickname'])
#             print(f'Followers: {uFollowers}')
            
            formatted = {
                'body':uBody,
                'created_at':uCreatedAt,
                'followers':uFollowers,
                'following':uFollowing,
                'likes':uLikes,
                'dislikes':uDislikes,
                'watchlist_stocks_count':uWatchListCount,
                'join_date':uJoinDate,
                'replies':uReplies,
                'sentiment':uSentiment,
                'sentiment_analysis':uSentimentAnalysis
            }
            body['comments'][uID] = formatted
            cc += 1
#             print(f'Comment {cc} done.\n')
            
        body['average_sentiment'] = totalSentiment/cc
        body['adjusted_sentiment'] = adjustedSentiment/sentimentDivider
        
        print('\n\n\n')
        print(f'Adj Sentiment: {adjustedSentiment/sentimentDivider}')
        print(f'Sentiment: {totalSentiment/cc}')
        
        old_data['last_comment'] = msgFirst['details']['userText']
        if DATE not in old_data.keys():
            old_data[DATE] = {}
            
        old_data[DATE][TIME] = body
        with open(f'./comments/yahoo/{self.ticker}.json','w') as JSON:
            json.dump(old_data,JSON)
            JSON.close()
    
    
    
    def parseStocktwitsComments(self, ticker):
        # Time interval: 30min
        data = {}
        try:
            with open(f'./comments/stocktwits/{ticker.upper()}.json','r') as JSON:
                data = json.load(JSON)
                JSON.close()
        except:
            print("This stock doesn't have any data yet.")
            return
        
        old_data = {}
        if os.path.isfile(f'./comments/p/stocktwits/{ticker.upper()}.json'):
            with open(f'./comments/p/stocktwits/{ticker.upper()}.json','r') as JSON:
                old_data = json.load(JSON)
                JSON.close()
            
        for line in data:
            if line == "last_comment":
                continue
            
            formatted = {}
            for timestamp in data[line]:
                tmp = {}
                hour = timestamp[0:2]
                minute = int(timestamp[3:5])
                
                if minute < 30:
                    minute = '00'
                else:
                    minute = '30'
                    
                tmp['first_last_delta'] = data[line][timestamp]['first_last_delta']
                tmp['average_sentiment'] = data[line][timestamp]['average_sentiment']
                tmp['adjusted_sentiment'] = data[line][timestamp]['adjusted_sentiment']
                
                formatted[hour+':'+minute] = tmp
                
            old_data[line] = formatted
            
        with open(f'./comments/p/stocktwits/{ticker.upper()}.json','w') as JSON:
            json.dump(old_data,JSON)
            JSON.close()

        print('Done.')
    
    
    
    
    def parseYahooComments(self, ticker):
        # Time interval: 30min
        data = {}
        try:
            with open(f'./comments/yahoo/{ticker.upper()}.json','r') as JSON:
                data = json.load(JSON)
                JSON.close()
        except:
            print("This stock doesn't have any data yet.")
            return
        
        old_data = {}
        if os.path.isfile(f'./comments/p/yahoo/{ticker.upper()}.json'):
            with open(f'./comments/p/yahoo/{ticker.upper()}.json','r') as JSON:
                old_data = json.load(JSON)
                JSON.close()
            
        for line in data:
            if line == "last_comment":
                continue
            
            formatted = {}
            for timestamp in data[line]:
                tmp = {}
                hour = timestamp[0:2]
                minute = int(timestamp[3:5])
                
                if minute < 30:
                    minute = '00'
                else:
                    minute = '30'
                    
                tmp['first_last_delta'] = data[line][timestamp]['first_last_delta']
                tmp['average_sentiment'] = data[line][timestamp]['average_sentiment']
                tmp['adjusted_sentiment'] = data[line][timestamp]['adjusted_sentiment']
                
                formatted[hour+':'+minute] = tmp
                
            old_data[line] = formatted
            
        with open(f'./comments/p/yahoo/{ticker.upper()}.json','w') as JSON:
            json.dump(old_data,JSON)
            JSON.close()

        print('Done.')
    
    
    def saveStocktwits(self):
        comments = self.getStocktwitsComments()
        self.saveStocktwitsComment(comments)
        
    def saveYahoo(self):
        comments = self.getYahooComments()
        self.saveYahooComment(comments)
    





#ticker = 'TSLA'
#cc = CommentSentiment(ticker,'newest')

#cc.saveStocktwits()
#cc.saveYahoo()

#cc.parseStocktwitsComments(ticker)
#cc.parseYahooComments(ticker)




