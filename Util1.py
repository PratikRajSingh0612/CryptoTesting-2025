
import requests
from cryptography.hazmat.primitives.asymmetric import ed25519
from urllib.parse import urlparse, urlencode
import urllib
import json
import time 
import datetime 
import pandas as pd
from cryptography.hazmat.primitives.asymmetric import ed25519
from tqdm import tqdm

import numpy as np
import matplotlib.pyplot as plt
import yfinance as yf
import numpy  # Import NaN explicitly
import pandas_ta as ta
from matplotlib.widgets import Slider
import plotly.graph_objects as go
from plotly.subplots import make_subplots

import math

import hmac
import hashlib
import base64


from joblib import Parallel, delayed
import multiprocessing

import warnings
from IPython.display import clear_output

pd.set_option('display.max_columns', None)

warnings.filterwarnings('ignore') 


def getBalance():
    # Enter your API Key and Secret here. If you don't have one, you can generate it from the website.
    key = myAPIKey
    secret = mySecretKey

    # python3
    secret_bytes = bytes(secret, encoding='utf-8')

    # Generating a timestamp
    timeStamp = int(round(time.time() * 1000))

    body = {
        "timestamp": timeStamp
    }

    json_body = json.dumps(body, separators = (',', ':'))

    signature = hmac.new(secret_bytes, json_body.encode(), hashlib.sha256).hexdigest()

    headers = {
        'Content-Type': 'application/json',
        'X-AUTH-APIKEY': key,
        'X-AUTH-SIGNATURE': signature
    }
    response = requests.post(balanceURL, data = json_body, headers = headers)
    data = response.json()
    data = pd.DataFrame(data)

    return(math.floor((data[data['currency'] ==  'USDT']['balance'].values)))



def getMarketDetails(marketDetailsURL):
    # Filter MarketDetails DataFrame to exclude unwanted pairs and include only those with 'market_order'
    response = requests.get(marketDetailsURL)
    MarketDetails = response.json()
    MarketDetails = pd.DataFrame(MarketDetails)

    exclude_pairs = ['KC-', 'USDC', 'ZBU', 'AGG', 'QI', 'MAHA', 'ANKR', 'BTTC', 'ZEN', 'QNT', 'ENA', 'VEMP', 'XR', 'DEFI', 'HAKA', 'OTK', 'STORE', 'VENOM', 'SAGA']
    MarketDetails = MarketDetails[
        MarketDetails['base_currency_short_name'].str.contains('usdt', case=False) &
        ~MarketDetails['pair'].str.contains('|'.join(exclude_pairs), case=False)
    ]

    MarketDetails['order_types'] = MarketDetails['order_types'].apply(','.join)
    MarketDetails = MarketDetails[MarketDetails['order_types'].str.contains('market_order', case=False)]
    return MarketDetails



def candlesDataExtract(pair, interval, BackTestEndTime):
    
    limit = 1000 # Default 500, Maximum 1000
    limit = str(limit)
    endTime = BackTestEndTime
    startTime = int(endTime - (24*60*60*1000))
    
    URLS = candlesURL + "&pair=" + pair + "&interval=" + interval + "&limit=" + limit + "&startTime=" + str(startTime) + "&endTime=" + str(endTime)
    # URLS = candlesURL + "&pair=" + pair + "&interval=" + interval + "&limit=" + limit

    try:
        response = requests.get(URLS)
        
        Candles = response.json()
        Candles = pd.DataFrame(Candles)
        Candles['pair'] = pair
        Candles = Candles.sort_values(by='time', ascending=True)
        #print(len(Candles))
    except:
        Candles = pd.DataFrame()

    # print(URLS)
    return Candles


# Getting the price of the particular crypto with its coin_pair
def check_price(pair):
    price_url = priceURL
    params = {
        "pair": pair,
        "limit": "1"
    }
    response = requests.get(price_url, params=params)
    # returning the price of that crypto
    return response.json()[0]["p"]


# Getting Market and candles data

def getAllCoin(pair_names, TimeforMarketData):

    i=1
    if i==1:
        marketCandles = pd.DataFrame()
        marketCandles = Parallel(n_jobs=-1)(delayed(candlesDataExtract)(i, TimeforMarketData, BackTestEndTime) for i in pair_names)
        marketCandles = list(marketCandles)
        marketCandles = pd.concat(marketCandles, ignore_index=True)
    
    marketCandles['date_time'] = pd.to_datetime(marketCandles['time']/1000 , unit='s').dt.strftime('%Y-%m-%d %H:%M:%S')
    marketCandles = marketCandles.sort_values(by='time', ascending=True)
    marketCandles.set_index('date_time', inplace=True)

    return marketCandles



def plot(PlotData):
    # Reference https://plotly.com/python/subplots/ https://pythoninoffice.com/draw-stock-chart-with-python/

    hist = PlotData.copy()

    hist['diff'] = hist['close'] - hist['open']
    hist.loc[hist['diff']>=0, 'color'] = 'green'
    hist.loc[hist['diff']<0, 'color'] = 'red'

    fig3 = make_subplots(rows=1, cols=1,
                        shared_xaxes=True,
                        vertical_spacing= 0.01)

    fig3.add_trace(go.Candlestick(x=hist.index,
                                open=hist['open'],
                                high=hist['high'],
                                low=hist['low'],
                                close=hist['close']
                                ), row=1, col=1)


    # Make it pretty
    fig3.update_layout(xaxis_rangeslider_visible=False)  #hide range slider
    fig3.update_layout(height=600, width=2000, autosize=True)
    fig3.update_yaxes(fixedrange = False)
    fig3.show()



