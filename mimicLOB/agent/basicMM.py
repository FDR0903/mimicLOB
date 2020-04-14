# -*- coding: utf-8 -*-
"""
Created on Thu Apr 12 19:01:34 2018

The basic Market Maker always fill the closest ticks to the mid price.

He does not control the imbalance. If there is no ask or bids, he fills them with two limits.

@author: Fayçal Drissi
"""

""" 
Imports
"""
from .genericAgent import genericAgent
from random import randint, randrange
from apscheduler.schedulers.background import BackgroundScheduler
from decimal import Decimal
import requests

class basicMM(genericAgent):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.JobSO = None
        self.JobCO = None
        
    #verify parameters ?
    def sendOrders(self):
        ticksize = requests.get(f"{self.server}/getticksize").json()['ticksize']

        Quantity = Decimal(self.dict_params['refQuantity'])
        RefPrice = Decimal(self.dict_params['refPrice'])
        HalfQuantity = Decimal(int(Quantity/2))
        # if no sellers, post some orders
        bestask = requests.get(f"{self.server}/getbestask").json()['bestask']
        bestbid = requests.get(f"{self.server}/getbestbid").json()['bestbid']
        if ((bestask is None) & (bestbid is None)):                
            # send ask & bid orders at 100 +- tick size
            self.send_buy_limit_order(Quantity, RefPrice-ticksize, None, 'marketMaker')
            self.send_buy_limit_order(HalfQuantity, RefPrice-2*ticksize, None, 'marketMaker')
            self.send_sell_limit_order(Quantity, RefPrice+ticksize, None, 'marketMaker')
            self.send_sell_limit_order(HalfQuantity, RefPrice+2*ticksize, None, 'marketMaker')
        elif bestask is None:
            # if self.lastTradePrice == 0:
            self.send_sell_limit_order(Quantity, bestbid+ticksize, None, 'marketMaker')
            self.send_sell_limit_order(HalfQuantity, bestbid+2*ticksize, None, 'marketMaker')
            
        elif bestbid is None:
            self.send_buy_limit_order(Quantity, bestask-ticksize, None, 'marketMaker')
            self.send_buy_limit_order(HalfQuantity, bestask-2*ticksize, None, 'marketMaker')

        else:
            # Control the spread with last trade price
            if bestask - bestbid > ticksize:
                # if last trade price is closest to bid, post ask orders. vice-versa
                lastTradePrice =  requests.get(f"{self.server}/getlastTradePrice").json()['lastTradePrice']
                lastlastTradeSign = requests.get(f"{self.server}/getlastTradeSign").json()['lastTradeSign']

                # post at last price and at the same direct as last trade sign / liquidity consumption
                if lastlastTradeSign=='bid':
                    qtty = requests.get(f"{self.server}/get_volume_at_price", 
                                    json={'side':'ask', 'price':bestask}).json()['volume']

                    self.send_buy_limit_order(qtty, lastTradePrice, None, 'marketMaker')
                else:
                    qtty = requests.get(f"{self.server}/get_volume_at_price", 
                                    json={'side':'bid', 'price':bestbid}).json()['volume']

                    self.send_sell_limit_order(qtty, lastTradePrice, None, 'marketMaker')
                
                # add liquidity
                if (lastTradePrice-bestbid > bestask-lastTradePrice): 
                    # post bids
                    i = 1
                    while bestbid+i*ticksize <= bestask:
                        self.send_buy_limit_order(Quantity, bestbid+i*ticksize, None, 'marketMaker')
                        i += 1   
                elif (lastTradePrice-bestbid < bestask-lastTradePrice):
                    # post asks
                    i = 0
                    while bestask-i*ticksize > bestbid:
                        self.send_sell_limit_order(Quantity, bestask-i*ticksize , None, 'marketMaker')
                        i += 1   
                # else:
                    
        # except:
        #     print('I couldn t market make bro')                

    def cancelFarAwayOrders(self):
        try:
            tickSize = requests.get(f"{self.server}/getticksize").json()['ticksize']
            keys_ = self.pendingorders.keys()
            nbTicks = self.nbOfTicksForCancelation 

            for key_ in keys_:
                order = self.pendingorders[key_]
                
                # if they are executed    
                #if they too far away
                side = order['side']
                price = order['price']

                # best price at side
                if side == 'bid':
                    bestPrice = requests.get(f"{self.server}/getbestbid").json()['bestbid']
                else:
                    bestPrice = requests.get(f"{self.server}/getbestask").json()['bestask']
                
                # if best price < nbTicks * tickSize, cancel
                if (((side=='bid') & (price < bestPrice - nbTicks*tickSize)) | ((side=='ask') & (price > bestPrice + nbTicks*tickSize))):
                    params = {'side':side, 'id':key_}
                    requests.get(f"{self.server}/cancelOrder",
                                    json=params).json()
                    del self.pendingorders[key_]
        except Exception as e:
            print(f'ERROR canceling far away orders {str(e)}')

    
        
            


