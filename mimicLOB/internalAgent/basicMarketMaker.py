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

class basicMarketMaker(genericAgent):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.JobSO = None
        self.JobCO = None
        
        #verify parameters ?
            
    def sendOrders(self):
        ticksize = self.orderbook.tick_size
        Quantity = Decimal(self.dict_params['refQuantity'])
        RefPrice = Decimal(self.dict_params['refPrice'])
        HalfQuantity = Decimal(int(Quantity/2))
        # if no sellers, post some orders
        bestask = self.orderbook.get_best_ask()
        bestbid = self.orderbook.get_best_bid()
        if ((bestask is None) & (bestbid is None)):                
            # send ask & bid orders at 100 +- tick size
            self.send_buy_limit_order(Quantity, RefPrice-ticksize, 0, 'marketMaker')
            self.send_buy_limit_order(HalfQuantity, RefPrice-2*ticksize, 0, 'marketMaker')
            self.send_sell_limit_order(Quantity, RefPrice+ticksize, 0, 'marketMaker')
            self.send_sell_limit_order(HalfQuantity, RefPrice+2*ticksize, 0, 'marketMaker')
        elif bestask is None:
            # if self.lastTradePrice == 0:
            self.send_sell_limit_order(Quantity, bestbid+ticksize, 0, 'marketMaker')
            self.send_sell_limit_order(HalfQuantity, bestbid+2*ticksize, 0, 'marketMaker')
            
        elif bestbid is None:
            self.send_buy_limit_order(Quantity, bestask-ticksize, 0, 'marketMaker')
            self.send_buy_limit_order(HalfQuantity, bestask-2*ticksize, 0, 'marketMaker')

        else:
            # Control the spread with last trade price
            if bestask - bestbid > ticksize:
                # if last trade price is closest to bid, post ask orders. vice-versa
                lastTradePrice = self.orderbook.lastTradePrice
                lastlastTradeSign = self.orderbook.lastTradeSign

                # post at last price and at the same direct as last trade sign / liquidity consumption
                if lastlastTradeSign=='bid':
                    qtty = self.orderbook.get_volume_at_price('ask', bestask)
                    self.send_buy_limit_order(qtty, lastTradePrice, 0, 'marketMaker')
                else:
                    qtty = self.orderbook.get_volume_at_price('bid', bestbid)
                    self.send_sell_limit_order(qtty, lastTradePrice, 0, 'marketMaker')
                
                # add liquidity
                if (lastTradePrice-bestbid > bestask-lastTradePrice): 
                    # post bids
                    i = 1
                    while bestbid+i*ticksize <= bestask:
                        self.send_buy_limit_order(Quantity, bestbid+i*ticksize, 0, 'marketMaker')
                        i += 1   
                elif (lastTradePrice-bestbid < bestask-lastTradePrice):
                    # post asks
                    i = 0
                    while bestask-i*ticksize > bestbid:
                        self.send_sell_limit_order(Quantity, bestask-i*ticksize , 0, 'marketMaker')
                        i += 1   
                # else:
                    
        # except:
        #     print('I couldn t market make bro')                

    def cancelFarAwayOrders(self):
        try:
            tickSize = self.orderbook.tick_size
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
                    bestPrice = self.orderbook.get_best_bid() 
                else:
                    bestPrice = self.orderbook.get_best_ask()
                
                # if best price < nbTicks * tickSize, cancel
                if (((side=='bid') & (price < bestPrice - nbTicks*tickSize)) | ((side=='ask') & (price > bestPrice + nbTicks*tickSize))):
                    self.orderbook.cancel_order(side, key_)
                    del self.pendingorders[key_]
        except Exception as e:
            print(f'ERROR canceling far away orders {str(e)}')

    def act(self):
        self.JobSO = self.orderbook.scheduler.add_job(self.sendOrders, 'interval', seconds=0.1, jitter=0.1)
        self.JobCO = self.orderbook.scheduler.add_job(self.cancelFarAwayOrders, 'interval', seconds=1, jitter=0.5) 

    def stop(self):
        if self.JobSO is not None:  self.JobSO.remove()       
        if self.JobCO is not None:  self.JobCO.remove()       
        self.JobSO = None
        self.JobCO = None
        
            


