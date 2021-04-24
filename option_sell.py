# -*- coding: utf-8 -*-
"""
Created on Sat Apr 24 10:18:44 2021

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
expiry_date= datetime.date(2021, 4, 29)
next_expiry_date = datetime.date(2021, 5, 6)