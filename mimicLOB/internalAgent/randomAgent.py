# -*- coding: utf-8 -*-
"""
Created on Thu Apr 12 19:01:34 2018

The random agent has a poisson intensity of sending orders, 
a type (buyer or seller), and an inventory.

The random agent sends random quantities between a range given in its construction.

If the random agent is a limit order sender, he sends half the quantity at each limit

@author: Fayçal Drissi
"""

""" 
Imports
"""
from .genericAgent import genericAgent
from random import randint, randrange
from decimal import Decimal
from apscheduler.schedulers.background import BackgroundScheduler
import sys
import numpy as np

class randomAgent(genericAgent):
    def __init__(self, **kwargs):
        super().__init__( **kwargs)
        intensity = self.dict_params['intensity']
        self.PoissonPath = np.random.poisson(intensity, 1000)
        self.Pathposition = 0
        self.newsChannel = self.dict_params['channel']
        self.JobSO = None # reference to the sending order job in the LOB scheduler
        self.JobCO = None # reference to the cancel order job in the LOB scheduler
        self.newsSources = None # news to which the agent listens to

    def sendOrders(self):
        if self.Pathposition == 1000: self.Pathposition = 0
        if self.PoissonPath[self.Pathposition] == 1:
            # either buyer or seller
            type_ = self.dict_params['subtype']
            quantityRange = self.dict_params['quantityRange'] #Should be an array  of 3 values : [min, max, step]
            minquantity = quantityRange[0]
            maxquantity = quantityRange[1]
            stepquantity = quantityRange[2]

            # Modulate quantity with news
            lastNews = self.newsChannel.get_latest_news()
            
            qtty = randrange(minquantity, maxquantity, stepquantity)
            ticksize = self.orderbook.tick_size
            
            if type_ == 'randomLimitBuyer':
                bestask = self.orderbook.get_best_ask()      
                bump = ((lastNews.val - 50) *2)/100 + 1      
                qtty = Decimal(int(qtty*bump))
                # post at bestask and some tick sizes randomly
                self.send_buy_limit_order(qtty, bestask-ticksize, 0, 0)

            elif type_ == 'randomMarketBuyer':
                bump = ((lastNews.val - 50) *2)/100 + 1        
                qtty = Decimal(int(qtty*bump))
                
                self.send_buy_market_order(qtty, 0)

            elif type_ == 'randomLimitSeller':
                bump = ((50 - lastNews.val) *2)/100 + 1          
                qtty = Decimal(int(qtty*bump))
                bestbid = self.orderbook.get_best_bid()

                # post at bestask and some tick sizes randomly
                self.send_sell_limit_order(qtty, bestbid+Decimal(ticksize), 0, 0)

            elif type_ == 'randomMarketSeller':
                bump = ((50 - lastNews.val) *2)/100 + 1              
                qtty = Decimal(int(qtty*bump))
                self.send_sell_market_order(qtty, 0)
            else:
                sys.exit('agent.ranndomagent.sendOrders() given a wrong type of basic random agent')

        self.Pathposition += 1
    
    def cancelFarAwayOrders(self):
        try:
            tickSize = float(self.orderbook.tick_size)
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
                    bestPrice = float(self.orderbook.get_best_bid())
                else:
                    bestPrice = float(self.orderbook.get_best_ask())
                
                # if best price < nbTicks * tickSize, cancel
                if (((side=='bid') & (price < bestPrice - nbTicks*tickSize)) | ((side=='ask') & (price > bestPrice + nbTicks*tickSize))):
                    self.orderbook.cancel_order(side, key_)
                    del self.pendingorders[key_]
        except Exception as e:
            print(f'ERROR canceling far away orders {str(e)}')
                
    def act(self):
        self.JobSO = self.orderbook.scheduler.add_job(self.sendOrders, 'interval', seconds=1, jitter=0.5)
        self.JobCO = self.orderbook.scheduler.add_job(self.cancelFarAwayOrders, 'interval', seconds=1, jitter=0.5)

    def stop(self):
        if self.JobSO is not None:  self.JobSO.remove()       
        if self.JobCO is not None:  self.JobCO.remove()       
        self.JobSO = None
        self.JobCO = None     

