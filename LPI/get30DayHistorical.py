import datetime
import os
import json
import requests


def getHistoricalMinuteData(TICKER,DAYS):
    API_KEY = '404c375143b0328d7a849afff5ca69b2'
    TYPE = 'minutes'
    
    mydatetime = datetime.datetime.now()
    before = mydatetime - datetime.timedelta(days=DAYS)
    year = str(before)[0:4]
    month = str(before)[5:7]
    day = str(before)[8:10]
    START = int(year + month + day + '000000')
    
    URL = f'https://marketdata.websol.barchart.com/getHistory.csv?apikey={API_KEY}&symbol={TICKER}&type={TYPE}&startDate={START}'
    
    html = requests.get(URL)
    data = [i.split(',') for i in html.text.replace('\r','').split('\n')]
    
    old_data = {}
    if os.path.isfile(f'./stock/1d/{TICKER}.json'):
        with open(f'./stock/1d/{TICKER}.json','r') as JSON:
            old_data = json.load(JSON)
    
    for info in data[1:-1]:
        time_ = info[1][1:-1].split('T')[1][0:5]
        date_ = info[2][1:-1]
        open_ = float(info[3][1:-1])
        high_ = float(info[4][1:-1])
        low_ = float(info[5][1:-1])
        close_ = float(info[6][1:-1])
        volume_ = int(info[7][1:-1])
        formatted = {'price':open_,'open':open_,'close':close_,'high':high_,'low':low_,'volumeDelta':volume_}
        
        try:
            old_data[date_][time_] = formatted
        except:
            old_data[date_] = {}
            old_data[date_][time_] = formatted
            
    with open(f'./stock/1d/{TICKER}.json','w') as JSON:
        old_data = json.dump(old_data,JSON)

