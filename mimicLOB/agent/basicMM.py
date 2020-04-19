# -*- coding: utf-8 -*-
"""
Created on Thu Apr 12 19:01:34 2018

The basic Market Maker always fill the closest ticks to the mid price.

He does not control the imbalance. If there is no ask or bids, he fills them with two limits.

@author: FDR
"""

""" 
Imports
"""
from .genericAgent import genericAgent
from random import randint, randrange
from apscheduler.schedulers.background import BackgroundScheduler
from decimal import Decimal
import requests
from sortedcontainers import SortedDict

class basicMM(genericAgent):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.JobSO = None
        self.JobCO = None
        self.nbOfTicksForCancelation = 10 if 'nbOfTicksForCancelation' not in self.dict_params else self.dict_params['nbOfTicksForCancelation']

        self.myOrders = SortedDict() # only for random agent that must keep track of his orders
        self._i_myorders = -1
    
    @property
    def i_myorders(self):
        self._i_myorders += 1
        return self._i_myorders

    #verify parameters ?
    def sendOrders(self):
        ticksize = self.getTickSize()

        Quantity = Decimal(self.dict_params['refQuantity'])
        RefPrice = Decimal(self.dict_params['refPrice'])
        HalfQuantity = Decimal(int(Quantity/2))
        # if no sellers, post some orders
        bestask = self.getBestAsk()
        bestbid = self.getBestBid()
        if ((bestask is None) & (bestbid is None)):                
            # send ask & bid orders at 100 +- tick size
            self.send_buy_limit_order(Quantity, RefPrice-ticksize)
            self.send_buy_limit_order(HalfQuantity, RefPrice-2*ticksize)
            self.send_sell_limit_order(Quantity, RefPrice+ticksize)
            self.send_sell_limit_order(HalfQuantity, RefPrice+2*ticksize)

            self.myOrders[self.i_myorders] = {'side' :'bid', 'price' : RefPrice-ticksize}
            self.myOrders[self.i_myorders] = {'side' :'bid', 'price' : RefPrice-2*ticksize}
            self.myOrders[self.i_myorders] = {'side' :'ask', 'price' : RefPrice+ticksize}
            self.myOrders[self.i_myorders] = {'side' :'ask', 'price' : RefPrice+2*ticksize}
        elif bestask is None:
            # if self.lastTradePrice == 0:
            self.send_sell_limit_order(Quantity, bestbid+ticksize)
            self.send_sell_limit_order(HalfQuantity, bestbid+2*ticksize)
            self.myOrders[self.i_myorders] = {'side' :'ask', 'price' : bestbid+ticksize}
            self.myOrders[self.i_myorders] = {'side' :'ask', 'price' : bestbid+2*ticksize}
        elif bestbid is None:
            self.send_buy_limit_order(Quantity, bestask-ticksize)
            self.send_buy_limit_order(HalfQuantity, bestask-2*ticksize)
            self.myOrders[self.i_myorders] = {'side' :'bid', 'price' : bestask-ticksize}
            self.myOrders[self.i_myorders] = {'side' :'bid', 'price' : bestask-2*ticksize}
        else:
            # Control the spread with last trade price
            if bestask - bestbid > ticksize:
                # if last trade price is closest to bid, post ask orders. vice-versa
                lastTradePrice = self.getlastTradePrice()
                lastlastTradeSign = self.getlastTradeSign()

                # post at last price and at the same direct as last trade sign / liquidity consumption
                if lastlastTradeSign=='bid':
                    qtty = self.get_volume_at_price('ask', bestask)
                    self.send_buy_limit_order(qtty, lastTradePrice)
                    self.myOrders[self.i_myorders] = {'side' :'bid', 'price' : lastTradePrice}

                else:
                    qtty = self.get_volume_at_price('bid', bestbid)
                    self.send_sell_limit_order(qtty, lastTradePrice)
                    self.myOrders[self.i_myorders] = {'side' :'ask', 'price' : lastTradePrice}
                
                # add liquidity
                if (lastTradePrice-bestbid > bestask-lastTradePrice): 
                    # post bids
                    i = 1
                    while bestbid+i*ticksize <= bestask:
                        self.send_buy_limit_order(Quantity, bestbid+i*ticksize)
                        self.myOrders[self.i_myorders] = {'side' :'bid', 'price' : bestbid+i*ticksize}
                        i += 1   
                elif (lastTradePrice-bestbid < bestask-lastTradePrice):
                    # post asks
                    i = 0
                    while bestask-i*ticksize > bestbid:
                        self.send_sell_limit_order(Quantity, bestask-i*ticksize)
                        self.myOrders[self.i_myorders] = {'side' :'ask', 'price' : bestask-i*ticksize}
                        
                        i += 1   
                # else:
                    
        # except:
        #     print('I couldn t market make it bro')                

    def start(self, sched):
        self.jobSO = sched.add_job(self.sendOrders, 'interval', seconds=0.0005, jitter=0.1, max_instances=1)
        self.JobCO = sched.add_job(self.cancelFarAwayOrders, 'interval', seconds=1, jitter=0.5, max_instances=1) 
    
    def stop(self, sched):
        if self.JobSO:  self.JobSO.remove()       
        if self.JobCO:  self.JobCO.remove()    
        self.JobSO = None
        self.JobCO = None

    def cancelFarAwayOrders(self):
        try:
            tickSize = self.getTickSize()
            keys_ = self.myOrders.keys()
            nbTicks = self.nbOfTicksForCancelation 

            for key_ in list(keys_): # transformed to list on purpose
                order = self.myOrders[key_]
                
                # if they are executed    
                #if they too far away
                side = order['side']
                price = order['price']

                # best price at side
                if side == 'bid':
                    bestPrice = self.getBestBid()
                else:
                    bestPrice = self.getBestAsk()
                
                if bestPrice is not None:
                    # if best price < nbTicks * tickSize, cancel
                    if (((side=='bid') & (price < bestPrice - nbTicks*tickSize)) | ((side=='ask') & (price > bestPrice + nbTicks*tickSize))):
                        self.cancelOrder(side, key_)
        except Exception as e:
            print(f'ERROR canceling far away orders {str(e)}')

    
        
            


