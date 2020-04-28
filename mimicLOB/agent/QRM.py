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
from sortedcontainers import SortedDict
from random import random

class QRM(genericAgent):
    def __init__(self, **kwargs):
        super().__init__( **kwargs)
        # Columns should be :
        # [ORDER_ID, PRICE, QTY, ORDER_SIDE, ORDER_TYPE, ACTION_TYPE]
        self._lambdas_plus  = self.dict_params['lambdas_plus']
        self._lambdas_minus = self.dict_params['lambdas_minus']
        self._event_sizes   = self.dict_params['event_sizes']

        self._qis = list(self._lambdas_plus.columns) # qi as a multiplier of AES
        self._queues = list(self._lambdas_plus.index)

        self._nbqueues  = int(len(self._lambdas_plus.index)/2)
        self.__maxqi = self._lambdas_plus.columns[-1]
        self.__minqi = self._lambdas_plus.columns[0]

        self._verbose2 = False

        # generate paths
        self.__paths_plus = {}
        self.__paths_minus = {}

        # previous mid price & ref price
        self._prev_midprice = 0
        self._prev_refprice = 0        

        # First price if LOB is empty
        self._S0 = self.dict_params['S0']

        # thetas
        self._theta   = self.dict_params['theta'] 
        self._theta_reinit   = self.dict_params['theta_reinit'] 
        
        # verbose
        self._verbose   = self.dict_params['verbose'] if 'verbose' in self.dict_params else False 

        # time counter
        self._itimestamp = -1 # if intensities are given in 

        # for every (qi, queue), generate poisson paths (waiting times), when it gets consumed, regenarates        
        for queue in self._queues:
            self.__paths_plus[queue] = {}
            self.__paths_minus[queue] = {}
            
            for qi in self._qis:
                self.__paths_plus[queue][qi] = {'i': 0, 'path':np.random.poisson(self._lambdas_plus.loc[queue, qi], 1000)}
                self.__paths_minus[queue][qi] = {'i': 0, 'path':np.random.poisson(self._lambdas_minus.loc[queue, qi], 1000)}
        
        # Obligatory storing of positions !
        self._b_record = True

    @property
    def itimestamp(self):
        self._itimestamp += 1
        return self._itimestamp

    # # Method to decide if whether we reinitialize the lob when the ref price changes
    # def draw_invariant_dist(self):
    #     return 0

    # do I have to add liquidity to the queue number i_queue
    # convention for i_queue, if side==bid, i_queue=1 means first queue, 2 means second. 
    def act_plus(self, side, qi, queue):
        if self._verbose:
            print(f"curr_waiting_time for adding to queue : {queue}, side : {side}, with size {qi}")

        # get the path
        path_waiting_times = self.__paths_plus[queue][qi]['path']

        # get the current waiting time
        curr_waiting_time = path_waiting_times[self.__paths_plus[queue][qi]['i']]
        if self._verbose:
            print(curr_waiting_time)

        # if it's 0 act, otherwise wait
        if curr_waiting_time ==0:
            self.__paths_plus[queue][qi]['i'] += 1

            # if we already been through the 1000 simulated waiting times, regenarate a path
            if self.__paths_plus[queue][qi]['i'] == 1000:
                self.__paths_plus[queue][qi] = {'i': 0, 'path':np.random.poisson(self._lambdas_plus.loc[queue, qi], 1000)}

            return True
        else:
            path_waiting_times[self.__paths_plus[queue][qi]['i']] -= 1
            return False

    def act_minus(self, side, qi, queue):
        if self._verbose:
            print(f"\ncurr_waiting_time for canceling from queue : {queue}, side : {side}, with size {qi}")

        # get the path
        path_waiting_times = self.__paths_minus[queue][qi]['path']

        # get the current waiting time
        curr_waiting_time = path_waiting_times[self.__paths_minus[queue][qi]['i']]
        if self._verbose:
            print(curr_waiting_time)

        # if it's 0 act, otherwise wait
        if curr_waiting_time ==0:
            self.__paths_minus[queue][qi]['i'] += 1

            # if we already been through the 1000 simulated waiting times, regenarate a path
            if self.__paths_minus[queue][qi]['i'] == 1000:
                self.__paths_minus[queue][qi] = {'i': 0, 'path':np.random.poisson(self._lambdas_minus.loc[queue, qi], 1000)}

            return True
        else:
            path_waiting_times[self.__paths_minus[queue][qi]['i']] -= 1
            return False
    
    @property
    def lambdas_plus(self):
        return self._lambdas_plus
    @property
    def lambdas_minus(self):
        return self._lambdas_minus
    @property
    def event_sizes(self):
        return self._event_sizes

    # this method is called at each time step i (considered dt = 1)
    def sendOrders(self):
        # all orders of this round come at the same timestamp : 
        itimestamp = self.itimestamp

        # get ref price
        bestbid = self.getBestBid()
        bestask = self.getBestAsk()
        tickSize = self.getTickSize()

        if bestbid and not bestask:
            self._prev_refprice = float(bestbid) + float(tickSize)/2
            curr_midprice = float(bestbid) + float(tickSize)/2
            bestask = float(bestbid + tickSize)

        elif bestask and not bestbid:
            self._prev_refprice = float(bestask) - float(tickSize)/2
            curr_midprice = float(bestask) - float(tickSize)/2
            bestbid = float(bestask) - float(tickSize)

        elif not bestbid and not bestask:
            if self._prev_refprice==0: 
                self._prev_refprice = self._S0 + float(tickSize)/2 #self._refprices[int(len(self._refprices)/2)]
                curr_midprice = self._S0 + float(tickSize)/2
                bestbid = self._S0
                bestask = self._S0 + tickSize
            else:
                curr_midprice = self._prev_midprice

        else:
            curr_midprice = float((bestask+bestbid)/2)

            # if ((bestask-bestbid)/tickSize) % 2:
            #     curr_refprice = float((bestask+bestbid)/2)
            # else:
            #     newrefprice1 = curr_midprice+float(tickSize)/2
            #     newrefprice2 = curr_midprice-float(tickSize)/2
            #     if np.abs(self._prev_refprice-newrefprice1) < np.abs(self._prev_refprice-newrefprice2):
            #         curr_refprice = newrefprice1
            #     else:
            #         curr_refprice = newrefprice2

        # if the mid price changed, assess if the ref price changed too
        if curr_midprice != self._prev_midprice:
            if random() < self._theta:
                
                # change the mid price
                curr_refprice = self._prev_refprice + float(tickSize) if curr_midprice > self._prev_midprice else self._prev_refprice - float(tickSize)

                if self._verbose2:
                    print(f'\nI m changing the ref price from {self._prev_refprice} to {curr_refprice}')

                # do we redraw new LOB ?
                if random() < self._theta_reinit:
                    if self._verbose2:
                        print(f'\nI m redrawing a new LOB around {curr_refprice}')
                    # clear lob 
                    self.orderbook.resetLOB()
            else:
                curr_refprice = self._prev_refprice
        else:
            curr_refprice = self._prev_refprice

        if random() < 0.1:
            if self._verbose2:
                print(f'\nI m redrawing a new LOB around {curr_refprice}, just like that')
            self.orderbook.resetLOB()

        if self._verbose:
            print('\n***************** STARTS *******************')
            print(f'ref price {curr_refprice}, best bid :{bestbid}, best ask {bestask}')
            print('***************** ****** *******************\n')

        # for every queue, if you have to act, send orders, or cancel last sent order
        # start with liquidity provision
        for i in range(self._nbqueues):
            # get the price of the bid queue
            bidprice = curr_refprice - i*float(tickSize) - 0.5*float(tickSize)
            askprice = curr_refprice + i*float(tickSize) + 0.5*float(tickSize)
            bid_queue_ = f'BID{i}'
            ask_queue_ = f'ASK{i}'

            # get quantity at limit :
            qi_bid = np.ceil(float(self.getVolumeAtPrice('bid', bidprice)) / self.event_sizes[bid_queue_])
            qi_ask = np.ceil(float(self.getVolumeAtPrice('ask', askprice)) / self.event_sizes[ask_queue_])

            if qi_bid > self.__maxqi: qi_bid = self.__maxqi
            if qi_ask > self.__maxqi: qi_ask = self.__maxqi

            if self.act_minus('bid', qi_bid, bid_queue_):
                # cancel a limit order
                qtty = np.ceil(self.event_sizes[bid_queue_])
                if self._verbose: print(f'I m canceling {qtty} bids @{bidprice}')
                self.cancel_an_order_at_limit(qtty, 'bid', bidprice, itimestamp)

            if self.act_minus('ask', qi_ask, ask_queue_):
                # cancel a limit order
                qtty = np.ceil(self.event_sizes[ask_queue_])
                if self._verbose: print(f'I m canceling {qtty} asks @{askprice}')
                self.cancel_an_order_at_limit(qtty, 'ask', askprice, itimestamp)

            # don t add il max
            if qi_bid < self.__maxqi:
                # start withy closest queue 
                if self.act_plus('bid', qi_bid, bid_queue_):
                    # send a limit order
                    qtty = np.ceil(self.event_sizes[bid_queue_])

                    if self._verbose: print(f'I m sending {qtty} bids @{bidprice}')
                    self.send_buy_limit_order(qtty, bidprice, timestamp=itimestamp)

            if qi_ask < self.__maxqi:
                if self.act_plus('ask', qi_ask, f'ASK{i}'):
                    # send a limit order
                    qtty = np.ceil(self.event_sizes[ask_queue_])
                    if self._verbose: print(f'I m sending {qtty} asks @{askprice}')
                    self.send_sell_limit_order(qtty, askprice, timestamp=itimestamp)

            

        self._prev_midprice = curr_midprice
        self._prev_refprice = curr_refprice
        
        # if the send orders are being activated by a scheduler
        if itimestamp > self.maxruns:
            print('******* Simulation OVER *******')
            self.sched.pause()

    def cancel_an_order_at_limit(self, qtty_to_cancel, side, price, itimestamp):
        remaining_qtty = qtty_to_cancel
        pendingorders_ids = list(self.pendingorders.keys())
        for key_ in pendingorders_ids:

            order = self.pendingorders[key_]
            
            if remaining_qtty==0:
                break

            if ((order['side'] == side) & (order['price'] == price)):
                if order['quantity'] > remaining_qtty:
                    self.modifyOrder(order_id     = key_, 
                                     side         = side,
                                     new_price    = order['price'],
                                     new_quantity = int(order['quantity'] - remaining_qtty),
                                     timestamp    = itimestamp)
                    remaining_qtty = 0
                    break
                else:
                    self.cancelOrder(side, key_)
                    remaining_qtty -= order['quantity']
        
        if remaining_qtty>0:
            if self._verbose: print('I CANCELED ALL THE QUEUE !!!')
    
    def start(self, sched, maxruns):
        self.sched = sched
        self.maxruns = maxruns
        self.job = sched.add_job(self.sendOrders, 'interval', seconds=0.0005, jitter=0.0001,  max_instances=1)

    def stop(self):
        if self.job:  self.job.remove()       
        self.job = None
