# -*- coding: utf-8 -*-
"""
Created on Sat Jan  2 16:32:07 2021

@author: quantum
"""

import yfinance as yf
from finta import TA
import pandas as pd
import numpy as np

import time
from alphatrade import AlphaTrade, LiveFeedType,OrderType,ProductType,TransactionType
import config
import datetime


TIMEFRAME = '15m'
boxp = 7
buffer = 5 
position = [False,False]
nifty = False
positions= [[],[]]
ltp =0
expiry_date= datetime.date(2021, 2, 11)

sas = AlphaTrade(login_id=config.login_id, password=config.password, twofa=config.twofa)





#print("Script Start Time :: " + str(datetime.datetime.now()))

def SuperTrend(df, name,period = 10, multiplier=2, ohlc=['open', 'high', 'low', 'close','EMA_5']):
    #small variation from jignesh patel supertrend indicator
    atr = 'ATR_' + str(period)
    st = 'ST'+name #+ str(period) + '_' + str(multiplier)
    stx = 'STX'+ name #  + str(period) + '_' + str(multiplier)

    # Compute basic upper and lower bands
    df['basic_ub'] = (df[ohlc[4]])  + multiplier * df[atr]
    df['basic_lb'] = (df[ohlc[4]])  - multiplier * df[atr]

    # Compute final upper and lower bands
    df['final_ub'] = 0.00
    df['final_lb'] = 0.00
    for i in range(period, len(df)):
        df['final_ub'].iat[i] = max(df['basic_ub'].iat[i-1],df['basic_ub'].iat[i]) if df['basic_ub'].iat[i] < df['final_ub'].iat[i - 1] or \
                                                         df[ohlc[4]].iat[i - 1] > df['final_ub'].iat[i - 1] else \
        df['final_ub'].iat[i - 1]
        df['final_lb'].iat[i] = min(df['basic_lb'].iat[i-1],df['basic_lb'].iat[i]) if df['basic_lb'].iat[i] > df['final_lb'].iat[i - 1] or \
                                                         df[ohlc[4]].iat[i - 1] < df['final_lb'].iat[i - 1] else \
        df['final_lb'].iat[i - 1]

    # Set the Supertrend value
    df[st] = 0.00
    for i in range(period, len(df)):
        df[st].iat[i] = df['final_ub'].iat[i] if df[st].iat[i - 1] == df['final_ub'].iat[i - 1] and df[ohlc[3]].iat[i] <= df['final_ub'].iat[i] else \
            df['final_lb'].iat[i] if df[st].iat[i - 1] == df['final_ub'].iat[i - 1] and df[ohlc[3]].iat[i] > \
                                     df['final_ub'].iat[i] else \
                df['final_lb'].iat[i] if df[st].iat[i - 1] == df['final_lb'].iat[i - 1] and df[ohlc[3]].iat[i] >= \
                                         df['final_lb'].iat[i] else \
                    df['final_ub'].iat[i] if df[st].iat[i - 1] == df['final_lb'].iat[i - 1] and df[ohlc[3]].iat[i] < \
                                             df['final_lb'].iat[i] else 0.00

        # Mark the trend direction up/down
    df[stx] = np.where((df[st] > 0.00), np.where((df[ohlc[3]] < df[st]), 'down', 'up'), np.NaN)

    # Remove basic and final bands from the columns
    df.drop(['basic_ub', 'basic_lb', 'final_ub', 'final_lb'], inplace=True, axis=1)

    df.fillna(0, inplace=True)
    return df

def setstuff(x):
    x[0]= 1
    a=[]
    for idx , val in enumerate(x):
        if val == 0.0:
            y=a[-1]
            a.append(y)   
        else:
            a.append(val)
    return np.array(a)


def get_data(symbol):
    symbol=symbol
    df = yf.download( symbol, period='3d', interval= TIMEFRAME )
    df.columns = ['open', 'high', 'low', 'close', 'Adj Close', 'volume']
    df.reset_index(inplace=True)
    df['ll'] = df['low'].rolling(window=boxp).min()
    df['k1'] = df['high'].rolling(window=boxp).max()
    df['box1'] = np.greater(df['high'].rolling(window=boxp-1).max(),df['high'].rolling(window=boxp-2).max())
    df=pd.concat([df,TA.ATR(df,10)], axis=1)
    df=pd.concat([df,TA.ATR(df,5)], axis=1)
    df.drop(['Adj Close'], inplace=True, axis=1)
    df.rename(columns = {"10 period ATR":'ATR_' + str(10)}, inplace = True)
    df.rename(columns = {"5 period ATR":'ATR_' + str(5)}, inplace = True)
    df=pd.concat([df,TA.EMA(df,5)], axis=1)
    df.rename(columns = {"5 period EMA":'EMA_' + str(5)}, inplace = True)
    df=pd.concat([df,TA.SAR(df)], axis=1)
    df.rename(columns = {0:'psar' }, inplace = True)
    df=SuperTrend(df,'s')
    df=SuperTrend(df,'f',period=5,multiplier=1)
    df["l_high"] = df["high"].rolling(boxp-1).apply(lambda x: x[0],raw=True)
    df["l_k1"] = df["k1"].rolling(boxp).apply(lambda x: x[0],raw=True)
    df['topbox'] = setstuff(np.where(np.logical_and(df["l_high"] > df["l_k1"] ,df['box1']), df["l_high"] , 0 ))
    df['bottombox'] = setstuff(np.where(np.logical_and(df["l_high"] > df["l_k1"] ,df['box1']), df["ll"] , 0 )) 
    df.drop(["l_high", "l_k1",'k1','box1','ll'], inplace=True, axis=1)
    return df

#(^NSEI)^NSEBANK

def buy_zerbra():
    global ltp
    x= int(ltp/100)*100
    global positions
    global nifty
    if nifty:
        symbol= 'NIFTY'
        val =300
        q= 75
    else:
        symbol= 'BANKNIFTY'
        val =700
        q=25
    deep_call = sas.get_instrument_for_fno(symbol = symbol, expiry_date=expiry_date, is_fut=False, strike=x-val, is_call = True)
    atm_call = sas.get_instrument_for_fno(symbol = symbol, expiry_date=expiry_date, is_fut=False, strike=x, is_call = True)
    y=(deep_call,atm_call)
    if nifty:
        positions[0].append(y)
    else:
        positions[1].append(y)
    buy_signal(deep_call,2*q)
    sell_signal(atm_call,q)

def square_off(x):
    global positions
    p=positions
    print("squaring off positions")
    if x:
        for i in p[0]:
            buy_signal(i[1],75)
            sell_signal(i[0],2*75)
            positions[0].remove(i)
        
    else:
        for i in p[1]:
            buy_signal(i[1],25)
            sell_signal(i[0],50)
            positions[1].remove(i)

def buy_signal(ins_scrip,q):
    global sas
    a=sas.place_order(transaction_type = TransactionType.Buy,
                         instrument = ins_scrip,
                         quantity = q,
                         order_type = OrderType.Market,
                         product_type = ProductType.Intraday,
                         price = 0.0,
                         trigger_price = None,
                         stop_loss = None,
                         square_off = None,
                         trailing_sl = None,
                         is_amo = False)
    
    print("buy",ins_scrip[2],a)

def sell_signal(ins_scrip,q):
    global sas
    a=sas.place_order(transaction_type = TransactionType.Sell,
                         instrument = ins_scrip,
                         quantity = q,
                         order_type = OrderType.Market,
                         product_type = ProductType.Intraday,
                         price = 0.0,
                         trigger_price = None,
                         stop_loss = None,
                         square_off = None,
                         trailing_sl = None,
                         is_amo = False)
    print("sell",ins_scrip[2],a)
    

def dravs(ohlc):
    buy , sell = False , False
    global position
    global ltp 
    global nifty
    ltp = ohlc['close'].values[-1]
    topbox , bottombox = ohlc['topbox'].values[-1]+buffer , ohlc['bottombox'].values[-1]-buffer
    if ohlc['close'].values[-1] > topbox and ohlc['close'].values[-3] < topbox:
        buy =True
    if ohlc['close'].values[-1] < bottombox and ohlc['close'].values[-3] > bottombox:
        sell =True
    if ohlc['STXs'].values[-1] == 'up' and buy and ((nifty == True and position[0] == False)or (nifty== False and position[1]== False)):
        if nifty:
            position[0] = True
        else:
            position[1] = True
        buy_zerbra()
        print('buy logic')
    if ohlc['STXs'].values[-1] == 'down' and sell:
        print('sell logic')
    if ohlc['STXf'].values[-1] == 'up' and ohlc['STXf'].values[-3] == 'down' :
        print('stop sell')
    if (((ohlc['STXs'].values[-1] == 'down' and ohlc['STXs'].values[-3] == 'up' ) or ohlc["psar"].values[-1] > ohlc["close"].values[-1]) )and ((nifty == True and position[0] == True)or (nifty== False and position[1])):
        if nifty:
            square_off(nifty)
            position[0]=False
        else:
            square_off(False)
            position[1]=False
        
        print('stop buy')
    print(topbox,bottombox)



def run():
    global runcount
    global positions
    global nifty
    start_time = int(9) * 60 + int(15)  # specify in int (hr) and int (min) foramte
    end_time = int(15) * 60 + int(10)  # do not place fresh order
    stop_time = int(15) * 60 + int(15)  # square off all open positions
    last_time = start_time
    schedule_interval = 900  # run at every 15 min
    runcount = 0
    while True:
        if ((datetime.datetime.now().hour * 60 + datetime.datetime.now().minute) >= end_time) :
            if (datetime.datetime.now().hour * 60 + datetime.datetime.now().minute) >= stop_time:
                square_off(True)
                square_off(False)
                print( "Trading day closed, time is above stop_time")
                break

        elif (datetime.datetime.now().hour * 60 + datetime.datetime.now().minute) >= start_time and datetime.datetime.now().minute%15==0:
            if time.time() >= last_time:
                last_time = time.time() + schedule_interval
                print("\n\n {} Run Count : Time - {} ".format(runcount, datetime.datetime.now()))
                if runcount >= 0:
                    try:
                        nifty = False
                        x=get_data('^NSEBANK')
                        dravs(x)
                        nifty = True
                        x=get_data('^NSEI')
                        dravs(x)
                        time.sleep(schedule_interval)
                        print("running ", datetime.datetime.now(),positions)
                    except Exception as e:
                        print("Run error", e)
                runcount = runcount + 1
        else:
            #print('     Waiting...', datetime.datetime.now())
            if datetime.datetime.now().minute%15 == 0:
                time.sleep(900)
            else:
                time.sleep((datetime.datetime.now().minute%15 * 60)-datetime.datetime.now().second)

run()