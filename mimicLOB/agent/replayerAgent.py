# -*- coding: utf-8 -*-
"""
Created on Thu Apr 12 19:01:34 2018

The replayer agent replays historical orders

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

class replayerAgent(genericAgent):
    def __init__(self, **kwargs):
        super().__init__( **kwargs)
        # Columns should be : 
        # [ORDER_ID, PRICE, QTY, ORDER_SIDE, ORDER_TYPE, ACTION_TYPE]
        self._historicalOrders = self.dict_params['historicalOrders']
    
    @property
    def historicalOrders(self):
        return self._historicalOrders

    @historicalOrders.setter
    def historicalOrders(self, historicalOrders):
        self._historicalOrders = historicalOrders

    def replayOrders(self):
        for i in self.historicalOrders.index:

            #limit orders
            if ((self.historicalOrders.loc[i, 'ACTION_TYPE'] == 'I') | (self.historicalOrders.loc[i, 'ACTION_TYPE'] == 'T')):
                ordertype = 'market' if self.historicalOrders.loc[i, 'ORDER_TYPE']==1 else 'limit'
                side      = 'bid' if self.historicalOrders.loc[i, 'ORDER_SIDE']=='B' else 'ask'                
                order_id  = self.historicalOrders.loc[i, 'ORDER_ID']

                if ordertype=='market':
                    if side=='bid':
                        self.send_buy_market_order(quantity  = int(self.historicalOrders.loc[i, 'QTY']))
                    else:
                        self.send_sell_market_order(quantity = int(self.historicalOrders.loc[i, 'QTY']))
                else:
                    if side=='bid':
                        self.send_buy_limit_order(quantity  = int(self.historicalOrders.loc[i, 'QTY']),
                                                  price    = self.historicalOrders.loc[i, 'PRICE'],
                                                  order_id = order_id)
                    else:
                        self.send_sell_limit_order(quantity = int(self.historicalOrders.loc[i, 'QTY']),
                                                   price    = self.historicalOrders.loc[i, 'PRICE'],
                                                   order_id = order_id)

            #cancel orders
            elif self.historicalOrders.loc[i, 'ACTION_TYPE'] == 'C':
                side = 'bid' if self.historicalOrders.loc[i, 'ORDER_SIDE']=='B' else 'ask'
                order_id = int(self.historicalOrders.loc[i, 'ORDER_ID'])
                self.cancelOrder(side     = side, 
                                 order_id = order_id)
            
            #replace order
            elif ((self.historicalOrders.loc[i, 'ACTION_TYPE'] == 'R') |(self.historicalOrders.loc[i, 'ACTION_TYPE'] == 'r') |(self.historicalOrders.loc[i, 'ACTION_TYPE'] == 'S')):
                ordertype = 'market' if self.historicalOrders.loc[i, 'ORDER_TYPE']==1 else 'limit'
                side      = 'bid' if self.historicalOrders.loc[i, 'ORDER_SIDE']=='B' else 'ask'                
                order_id  = int(self.historicalOrders.loc[i, 'ORDER_ID'])

                self.modifyOrder(order_id     = order_id, 
                                 side         = side,
                                 new_price    = self.historicalOrders.loc[i, 'PRICE'],
                                 new_quantity = int(self.historicalOrders.loc[i, 'QTY']))
 