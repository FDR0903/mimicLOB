# -*- coding: utf-8 -*-
"""
Created on Thu Apr 12 19:01:34 2018

The random agent has a poisson intensity of sending orders, 
a type (buyer or seller), and an inventory.

The random agent sends random quantities between a range given in its construction.

If the random agent is a limit order sender, he sends half the quantity at each limit

@author: FDR
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
import requests
from sortedcontainers import SortedDict

class liquidityConsumerAgent(genericAgent):
    def __init__(self, **kwargs):
        super().__init__( **kwargs)
        intensities = self.dict_params['intensities']
        self.impliedNbAgents = len(intensities)

        self.PoissonPaths = {}
        for i in range(self.impliedNbAgents):
            self.PoissonPaths[i] = np.random.poisson(intensities[i], 1000)
    
        self.Pathposition = 0

        # self.newsChannel = self.dict_params['channel']
        self.JobSO = None # reference to the sending order job in the LOB scheduler
        self.JobCO = None # reference to the cancel order job in the LOB scheduler
        self.newsSources = None # news to which the agent listens to

        self._i_myorders = -1
        self.nbOfTicksForCancelation = 10 if 'nbOfTicksForCancelation' not in self.dict_params else self.dict_params['nbOfTicksForCancelation']
        self.newsChannel = self.dict_params['channel']

        self.lobticksize = Decimal(self.getTickSize())

    def getlastnews(self):
        # if self.distant:
        #     return requests.get(f"{self.server}/getlastnews").json()['lastnews']
        # else:
        return self.newsChannel.get_latest_news().val

    def start(self, sched):
        self.jobSO = sched.add_job(self.sendOrders, 'interval', seconds=0.005, jitter=0.001, max_instances=1)
        self.JobCO = sched.add_job(self.cancelFarAwayOrders, 'interval', seconds=1, jitter=0.5, max_instances=1) 
    
    def stop(self, sched):
        if self.JobSO:  self.JobSO.remove()       
        if self.JobCO:  self.JobCO.remove()    
        self.JobSO = None
        self.JobCO = None

    def sendOrders(self):
        if self.Pathposition == 1000: 
            self.Pathposition = 0
        # loop on 'agents'
        for i in range(self.impliedNbAgents):
            if self.PoissonPaths[i][self.Pathposition] == 1:
                # get tick (if it changed)
                self.lobticksize = Decimal(self.getTickSize())
                
                # either buyer or seller
                type_ = self.dict_params['subtypes'][i]
                quantityRange = self.dict_params['quantityRanges'][i] #Should be an array  of 3 values : [min, max, step]

                minquantity = quantityRange[0]
                maxquantity = quantityRange[1]
                stepquantity = quantityRange[2]

                # Modulate quantity with news
                lastNews = self.getlastnews()
                qtty = randrange(minquantity, maxquantity, stepquantity)
                
                if type_ == 'randomLimitBuyer':
                    bestask = self.getBestAsk()
                    bump = ((lastNews - 50) *2)/100 + 1      
                    qtty = Decimal(int(qtty*bump))
                    # post at bestask and some tick sizes randomly
                    if bestask: 
                        self.send_buy_limit_order(qtty, Decimal(bestask)-self.lobticksize)
                elif type_ == 'randomMarketBuyer':
                    bump = ((lastNews - 50) *2)/100 + 1        
                    qtty = Decimal(int(qtty*bump))
                    bestask = self.getBestAsk()
                    if bestask: 
                        self.send_buy_limit_order(qtty, Decimal(bestask))
                    # self.send_buy_market_order(qtty)

                elif type_ == 'randomLimitSeller':
                    bump = ((50 - lastNews) *2)/100 + 1          
                    qtty = Decimal(int(qtty*bump))
                    bestbid = self.getBestBid()

                    # post at bestask and some tick sizes randomly
                    if bestbid: self.send_sell_limit_order(qtty, Decimal(bestbid)+self.lobticksize)
                elif type_ == 'randomMarketSeller':
                    bump = ((50 - lastNews) *2)/100 + 1              
                    qtty = Decimal(int(qtty*bump))
                    bestbid = self.getBestBid()
                    if bestbid: 
                        self.send_sell_limit_order(qtty, Decimal(bestbid))
                else:
                    sys.exit('agent.ranndomagent.sendOrders() given a wrong type of basic random agent')

        self.Pathposition += 1
    
    def cancelFarAwayOrders(self):
        try:
            tickSize = Decimal(self.getTickSize())
            keys_ = self.pendingorders.keys()
            nbTicks = self.nbOfTicksForCancelation 

            for key_ in list(keys_): # transformed to list on purpose
                order = self.pendingorders[key_]
                
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
                    bestPrice = Decimal(bestPrice)
                    price = Decimal(price)

                    # if best price < nbTicks * tickSize, cancel
                    if (((side=='bid') & (price < bestPrice - nbTicks*tickSize)) | ((side=='ask') & (price > bestPrice + nbTicks*tickSize))):
                        self.cancelOrder(side, key_)
        except Exception as e:
            print(f'ERROR canceling far away orders {str(e)}')
                
 
