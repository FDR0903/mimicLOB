# -*- coding: utf-8 -*-
"""
Created on 16Feb2020

Agent : abstract class


@author: FDR
"""



# External Import
from abc import ABC, abstractmethod, ABCMeta
from sortedcontainers import SortedDict
import datetime
import requests
import time
import pandas as pd
import sys
from ..server import ngrok
from decimal import Decimal

class genericAgent(ABC):
    def __init__(self, **kwargs):
        self.__dict_params = kwargs 

       
        # Personal book
        self._b_record = self.__dict_params['b_record'] if 'b_record' in self.__dict_params else False
        self._usengrok = self.__dict_params['usengrok'] if 'usengrok' in self.__dict_params else False
        self._executedtrades = SortedDict()
        self._sentorders = SortedDict()
        self._pendingorders = SortedDict()
        # self._book = SortedDict()
        # self._trades = SortedDict()

         # Client/Server or direct
        self._distant = self.__dict_params['distant'] if 'distant' in self.__dict_params else False
        if self._distant:
            self._server = self.__dict_params['server'] # lob server
            if self._b_record:  
                if self._usengrok:
                    self._fixserver = ngrok.connect(self.__dict_params['FIXaddress'])
                else:
                    self._fixserver = self.__dict_params['FIXaddress']
                    if self._fixserver[-1] == '/':
                        self._fixserver = self._fixserver[:-1]

        else:
            self._orderbook = self.__dict_params['orderbook']

        # Personal ID
        self._id = self.__dict_params['id'] if 'id' in self.__dict_params else 'generic'

        # Compteurs
        self._i_trades = -1
        self._i_orders = -1

        # Subscribe to LOB
        if self._b_record:
            self.addAgent2LOB(self)        

    def addAgent2LOB(self, agent):
        if self.distant:
            params = {'id' : self._id,
                      'address' : self._fixserver,
            }
            requests.get(f"{self._fixserver}/setid",
                            json={'id':self.id})
            requests.get(f"{self.server}/addAgent2LOB",
                            json=params).json()['status']
        else:
            self.orderbook.addAgent(agent)

    """
    GETTERS
    """
    @property
    def FIXserver(self):
        return self._fixserver
    @property
    def id(self):
        return self._id

    @property
    def distant(self):
        return self._distant

    @property
    def i_trades(self):
        self._i_trades += 1
        return self._i_trades

    @property
    def i_orders(self):
        self._i_orders += 1
        return self._i_orders

    @property
    def orderbook(self):
        return self._orderbook

    @property
    def b_record(self):
        return self._b_record

    @property
    def pendingorders(self):
        if self.distant:
            return requests.get(f"{self._fixserver}/pendingorders").json()['pendingorders']
        else:
            return self._pendingorders

    @property
    def executedtrades(self):
        if self.distant:
            return requests.get(f"{self._fixserver}/executedtrades").json()['executedtrades']
        else:
            return self._executedtrades
        
    @property
    def dict_params(self):
        return self.__dict_params

    @property
    def server(self):
        return self._server

    @property
    def sentorders(self):
        if self.distant:
            return requests.get(f"{self._fixserver}/sentorders").json()['sentorders']
        else:
            return self._sentorders

    # @property
    # def trades(self):
        # return self._trades

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
    # @abstractmethod
    # def act(self):
        # return NotImplementedError('Should Implement val')
    

    """
    Generic methods 
    Todo : should add processing of executed order
    Todo : should make optional processing of orders
    Todo : Should make it possible to exec on book 
    """
    # time in nanoseconds
    def timestamp(self):
        return time.time_ns()
    
    def send_sell_limit_order(self, quantity, price, order_id=None, timestamp=None):
        # get best ask price, and post randomly between the price and -spread
        #bestask = self.orderbook.get_best_ask()
        sellorder =  {'type'      : 'limit', 
                      'side'      : 'ask', 
                      'quantity'  : quantity,
                      'price'     : price,
                      'trader_id' : self.id}
        
        if order_id:
            sellorder['order_id'] = order_id
        
        if timestamp:
            sellorder['timestamp'] = timestamp

        if self.distant:
            response = requests.get(f"{self.server}/sendOrder", 
                                        json=sellorder).json()
            trades   = response['trades']
            orders   = response['pendingOrders']
        else:
            trades, orders = self.orderbook.process_order(sellorder)

        self.addSentOrders(sellorder)

        # Should process 
        return 'SENT'


    def send_buy_limit_order(self, quantity, price, order_id=None, timestamp=None):
        # get best ask price, and post randomly between the price and -spread
        #bestask = self.orderbook.get_best_ask()
        buyorder =  {'type'      : 'limit', 
                     'side'      : 'bid', 
                     'quantity'  : quantity,
                     'price'     : price,
                     'trader_id' : self.id}
        
        if order_id:
            buyorder['order_id'] = order_id

        if timestamp:
            buyorder['timestamp'] = timestamp

        if self.distant:
            response = requests.get(f"{self.server}/sendOrder", 
                                        json=buyorder).json()
            trades   = response['trades']
            orders   = response['pendingOrders']
        else:
            trades, orders = self.orderbook.process_order(buyorder)

        self.addSentOrders(buyorder)

        # Should process 
        return 'SENT'

    
    def send_sell_market_order(self, quantity):
        # get best ask price, and post randomly between the price and -spread
        sellorder =  {'type' : 'market', 
                     'side' : 'ask',
                     'quantity'  : quantity,
                     'trader_id' : self.id}

        if self.distant:
            response = requests.get(f"{self.server}/sendOrder", 
                                        json=sellorder).json()
            trades   = response['trades']
            orders   = response['pendingOrders']
        else:
            trades, orders = self.orderbook.process_order(sellorder)

        self.addSentOrders(sellorder)

        # Should process 
        return 'SENT'

    def send_buy_market_order(self, quantity):
        # get best ask price, and post randomly between the price and -spread
        buyorder =  {'type' : 'market', 
                     'side' : 'bid', 
                     'quantity'  : quantity,
                     'trader_id' : self.id}

        if self.distant:
            response = requests.get(f"{self.server}/sendOrder", 
                                        json=buyorder).json()
            trades   = response['trades']
            orders   = response['pendingOrders']
        else:
            trades, orders = self.orderbook.process_order(buyorder)

        self.addSentOrders(buyorder)

        # Should process 
        return 'SENT'

    def modifyOrder(self, side, order_id, new_price, new_quantity, timestamp=None):
        order_update = {'type'      : 'limit', 
                        'side'      : side, 
                        'quantity'  : new_quantity,
                        'price'     : new_price,
                        'trader_id' : self.id}

        if timestamp:
            order_update['timestamp'] = timestamp

        if self.distant:
            params = {}
            params['order'] = order_update
            params['order_id'] = int(order_id)
            response = requests.get(f"{self.server}/modifyOrder", 
                        json=params).json()
            return response['status']
        else:
            self.orderbook.modify_order(order_id, order_update)
            return 'ORDER MODIFIED'

    def cancelOrder(self, side, order_id):
        if self.distant:
            params = {'side':side, 'id':int(order_id)}
            response = requests.get(f"{self.server}/cancelOrder",
                                    json=params).json()
            return response['status']
        else:
            self.orderbook.cancel_order(side, order_id)
            return "CANCELED"

    # only if order's quantity is reduced
    def notify_order_modification(self, order_update):
        if order_update:
            self.pendingorders[order_update['order_id']]['quantity'] = order_update['quantity']

    def notify_order_cancelation(self, side, order_id):
        if order_id:
            if order_id in self.pendingorders:
                del self.pendingorders[order_id]

            # add cancelation to sent orders
            self.sentorders[self.i_orders] = {'type'      : 'cancel', 
                                              'side'      : side,
                                              'trader_id' : self.id,
                                              'order_id'  : order_id}

    # This method is called by an LOB to notify that an order has been executed !
    def notify_orders_in_book(self, pendingOrder):
        if pendingOrder:
            self.pendingorders[pendingOrder['order_id']] = pendingOrder
        
    def addSentOrders(self, order):
        if self.b_record:
            if self.distant:
                if order:
                    response = requests.get(f"{self._fixserver}/addSentOrders", 
                                                json=order).json()
            else:
                if order:
                    self.sentorders[self.i_orders] = order

    # This method is called by an LOB to notify that an order has been executed !
    def notify_trades(self, trade, check_pending=True):
        if trade:
            self.executedtrades[self.i_trades] = trade
            
            # update pending orders : if a trade fills a pending order
            # it must be deleted from pendingOrders, otherwise, the
            # quantity must be reduced
            if trade['party1_id'] == self.id:
                order_id = trade['party1_order_id']
            elif trade['party2_id'] == self.id:
                order_id = trade['party2_order_id']
            else:
                sys.exit(f'Fatal Error : Notify for agent {self.id}')
            
            # if false, it means it is trades that has been executed
            # directly after sending (agressive limit order or market order)
            if check_pending:
                traded_quantity = trade['traded_quantity']
                
                self.pendingorders[order_id]['quantity'] -= traded_quantity
                
                if self.pendingorders[order_id]['quantity'] == 0: 
                    del self.pendingorders[order_id]

                elif self.pendingorders[order_id]['quantity'] < 0: 
                    sys.exit(f'Fatal Error 2 : Notify for agent {self.id}')

    
    def getTransactionTape(self):
        if self.distant:
            TransactionTape = requests.get(f"{self.server}/getTransactionTape").json()['TransactionTape']
            return pd.read_json(TransactionTape)        
        else:
            TransactionTape = pd.DataFrame({i: [tapeitem['time'],
                                        tapeitem['party1_id'], 
                                        tapeitem['party1_side'], 
                                        tapeitem['party1_order_id'], 
                                        tapeitem['party2_id'], 
                                        tapeitem['party1_side'],
                                        tapeitem['party2_order_id'],
                                        tapeitem['traded_price'], 
                                        tapeitem['traded_quantity']] for (i, tapeitem) in enumerate(self.orderbook.tape)}).T
            if len(TransactionTape)>0:
                TransactionTape.columns = ['time', 'party1_id', 'party1_side', 'party1_order_id', 
                                           'party2_id', 'party2_side', 'party2_order_id',
                                           'traded_price', 'traded_quantity']
            return TransactionTape
    
    def getPriceTape(self):
        if self.distant:
            histoPrices = requests.get(f"{self.server}/getPriceTape",).json()['PriceTape']
        else:
            histoPrices = self.orderbook.pricetape

        histoPrices = pd.DataFrame([histoPrices]).T; 
        histoPrices.columns = ['Prices']
        return histoPrices

    def getLOBTape(self):
        if self.distant:
            LOBtape = requests.get(f"{self.server}/getLOBTape",).json()['LOBTape']
            LOBtape = pd.DataFrame({i: tapeitem for (i, tapeitem) in enumerate(LOBtape)}).T
        else:
            LOBtape = pd.DataFrame({i: tapeitem for (i, tapeitem) in enumerate(self.orderbook.LOBtape)}).T
            
        cols = ['TIME', 'ORDER_ID', 'PRICE', 'QTY', 'ORDER_SIDE', 'ORDER_TYPE', 'ACTION_TYPE']

        for i in range(self.orderbook.maxEntries-1, -1, -1):
            cols += [f'BID{i}', f'BID_QTY{i}']
        for i in range(self.orderbook.maxEntries):
            cols += [f'ASK{i}', f'ASK_QTY{i}'] 
        LOBtape.columns = cols         

        return LOBtape

    def getLOBState(self):
        if self.distant:
            response = requests.get(f"{self.server}/getLOBstate")
            try:
                LOBstate = pd.read_json(response.json()['LOBstate'])
                return LOBstate
            except:
                return 'LOB is empty'
        else:
            return self.orderbook.getLOBstate() 

    def getTickSize(self):
        if self.distant:
            return  requests.get(f"{self.server}/getticksize").json()['ticksize']
        else:
            return self.orderbook.tick_size

    def getMidPrice(self):
        try:
            midPrice = (self.getBestAsk() + self.getBestBid())/2
        except:
            midPrice = None
        return midPrice

    def getBestAsk(self):
        if self.distant:
            return requests.get(f"{self.server}/getbestask").json()['bestask']
        else:
            return self.orderbook.get_best_ask() 
    
    def getVolumeAtPrice(self, side, price):
        if self.distant:
            return requests.get(f"{self.server}/getVolumeAtPrice").json()['volume']
        else:
            return self.orderbook.get_volume_at_price(side, price)

    def getBestBid(self):
        if self.distant:
            return requests.get(f"{self.server}/getbestbid").json()['bestbid']
        else:
            return self.orderbook.get_best_bid() 
    


    def setLOB_tickSize(self, ticksize):
        if self.distant:
            response = requests.get(f"{self.server}/setticksize", json={'ticksize':ticksize}).json()
            return response['status']    
        else:
            self.orderbook.tick_size = ticksize
    
    def setLOB_b_auction(self, b_auction):
        if self.id == 'market':
            if self.distant:
                response = requests.get(f"{self.server}/setb_auction",
                                        json = {'b_auction' : b_auction}).json()
                return response['status']              
            else:
                self.orderbook.b_auction = b_auction
        else:
            return 'Only the market can reset the LOB'
    def resetLOB_PendingOrders(self):
        if self.id=='market':
            if self.distant:
                response = requests.get(f"{self.server}/resetLOB").json()
                return response['status']    
            else:
                self.orderbook.resetLOB() 
                return 'DONE'
        else:
            return 'Only the market can reset the LOB'

    def getlastTradePrice(self):
        if self.distant:
            lastTradePrice =  requests.get(f"{self.server}/getlastTradePrice").json()['lastTradePrice']
        else:
            lastTradePrice = self.orderbook.lastTradePrice
        return lastTradePrice


    def getlastTradeSign(self):
        if self.distant:
            lastlastTradeSign = requests.get(f"{self.server}/getlastTradeSign").json()['lastTradeSign']
        else:
            lastlastTradeSign = self.orderbook.lastTradeSign
        return lastlastTradeSign

    def get_volume_at_price(self, side, price):
        if self.distant:
            return requests.get(f"{self.server}/get_volume_at_price", 
                                    json={'side':side, 'price':price}).json()['volume']
        else:
            return self.orderbook.get_volume_at_price(side, price)
        
    def resetLOB(self):
        if self.id=='market':
            if self.distant:
                response = requests.get(f"{self.server}/reset").json()
                return response['status']    
            else:
                self.orderbook.reset() 
                return 'DONE'
        else:
            return 'Only the market can reset the LOB'
