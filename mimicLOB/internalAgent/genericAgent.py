# -*- coding: utf-8 -*-
"""
Created on 16Feb2020

Agent : abstract class


@author: Fayçal DRISSI
"""



# External Import
from abc import ABC, abstractmethod, ABCMeta
from sortedcontainers import SortedDict
import datetime

class genericAgent(ABC):
    def __init__(self, **kwargs):
        self.__dict_params = kwargs
        self._orderbook = self.__dict_params['orderbook']
        self._executedtrades = SortedDict()
        self._sentorders = SortedDict()
        self._pendingorders = SortedDict()
        self._book = SortedDict()
        self._trades = SortedDict() 

    """
    GETTERS
    """
    @property
    def pendingorders(self):
        return self._pendingorders

    @property
    def executedtrades(self):
        return self._executedtrades
        
    @property
    def dict_params(self):
        return self.__dict_params
    @property
    def orderbook(self):
        return self._orderbook
    @property
    def sentorders(self):
        return self._sentorders
    @property
    def trades(self):
        return self._trades

    """
    SETTERS
    """
    @dict_params.setter
    def dict_params(self, dict_params):
        self.__dict_params = dict_params


    """
    Abstract methods
    """
    #must return a dataFrame not a series
    @abstractmethod
    def act(self):
        return NotImplementedError('Should Implement val')
    
    """
    Generic methods 
    Todo : should add processing of executed order
    Todo : should make optional processing of orders
    Todo : Should make it possible to exec on book 
    """
    def addTradesAndOrders(self, trades, pendingOrders):
        if pendingOrders is not None:
            self.pendingorders[pendingOrders['order_id']] = pendingOrders
        if trades is not None:
            for trade in trades:
                self.executedtrades[trade['party2'][0]] = trade  
    
    def send_sell_limit_order(self, quantity, price, timestamp, trader_id):
        # get best ask price, and post randomly between the price and -spread
        #bestask = self.orderbook.get_best_ask()
        sellorder =  {'type'      : 'limit', 
                      'side'      : 'ask', 
                      'quantity'  : quantity,
                      'price'     : price,
                      'trader_id'  : trader_id,
                      'timestamp' : timestamp}
        trades, orders = self.orderbook.process_order(sellorder, False)
        self.addTradesAndOrders(trades, orders)

        # Should process 
        return sellorder


    def send_buy_limit_order(self, quantity, price, timestamp, trader_id):
        # get best ask price, and post randomly between the price and -spread
        #bestask = self.orderbook.get_best_ask()
        buyorder =  {'type'      : 'limit', 
                     'side'      : 'bid', 
                     'quantity'  : quantity,
                     'price'     : price,
                     'trader_id'  : trader_id,
                     'timestamp' : timestamp}
        trades, orders = self.orderbook.process_order(buyorder, False)
        self.addTradesAndOrders(trades, orders)
        return buyorder

    def send_buy_market_order(self, quantity, trader_id):
        # get best ask price, and post randomly between the price and -spread
        buyorder =  {'type' : 'market', 
                     'side' : 'bid', 
                     'quantity' : quantity,
                     'trader_id' : trader_id}
        trades, orders = self.orderbook.process_order(buyorder, False)
        self.addTradesAndOrders(trades, orders)
        return buyorder

    def send_sell_market_order(self, quantity, trader_id):
        # get best ask price, and post randomly between the price and -spread
        sellorder =  {'type' : 'market', 
                     'side' : 'ask',
                     'quantity' : quantity,
                     'trader_id' : trader_id}
        trades, orders = self.orderbook.process_order(sellorder, False)
        self.addTradesAndOrders(trades, orders)
        return sellorder

    def generate_new_MarketSell(self, quantity, trader_id):
        # get best ask price, and post randomly between the price and -spread
        sellorder =  {'type' : 'market', 
                     'side' : 'ask', 
                     'quantity' : quantity,
                     'trader_id' : trader_id}
        trades, orders = self.orderbook.process_order(sellorder, False)
        self.addTradesAndOrders(trades, orders)
        return sellorder

    