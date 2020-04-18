import sys
import math
from collections import deque # a faster insert/pop queue
from six.moves import cStringIO as StringIO
from decimal import Decimal
import numpy as np
from .ordertree import OrderTree
import pandas as pd
import time
from .orderlist import OrderList
class OrderBook(object):
    def __init__(self,  **kwargs):
        
        # Defaulkt values if none given
        tick_size = kwargs['tick_size'] if 'tick_size' in kwargs else Decimal(1)
        b_tape =  kwargs['b_tape'] if 'b_tape' in kwargs else True
        b_tape_LOB  = kwargs['b_tape_LOB'] if 'b_tape_LOB' in kwargs else True
        verbose  = kwargs['verbose'] if 'verbose' in kwargs else True
        
        # Basic properties of the LOB
        self._name = 'LOB'
        self._tick_size = Decimal(tick_size)

        # Tapes
        self.tape = deque(maxlen=None) # Transaction tape, Index[0] is most recent trade
        self._LOBtape = deque(maxlen=None) # lob tape, is most recent trade

        self._pricetape = []
        self._qttytape = []
        self._tstape = []

        # Trees of asks & bids
        self._bids = OrderTree()
        self._asks = OrderTree()

        # Current values
        self._lastTradePrice = 0
        self._lastTradeSign = 'bid'
        self._last_tick = None
        self._last_timestamp = 0
        self._time = 0

        # Agent list : agents in this list are notified when trades are executed
        self._agentList = {}

        # Countings
        self._next_order_id = 0
        self._maxEntries = 15 #number of ticks stored in the LOB tape
        
        # Verbose
        self._verbose = verbose

        # booleans
        self._b_tape     = b_tape # tape transactions
        self._b_tape_LOB = b_tape_LOB # requires lot of memory and time consumption
        self._b_auction  = kwargs['b_auction'] if 'b_auction' in kwargs else False # Specifies if the LOB i s in auction mode

        # method of order processing
        if self.b_auction:
            self.process_order = self.process_order_during_auction
        else:
            self.process_order = self.process_order_during_continuous_trading


#########################################
# Accessors, Setter, and Destructors
#########################################
    @property
    def b_auction(self):
        return self._b_auction
    
    @property
    def maxEntries(self):
        return self._maxEntries
    @property
    def LOBtape(self):
        return self._LOBtape
    @property
    def b_tape_LOB(self):
        return self._b_tape_LOB
    @property
    def verbose(self):
        return self._verbose
    @property
    def b_tape(self):
        return self._b_tape
    @property
    def agentList(self):
        return self._agentList
    @property
    def pricetape(self):
        return self._pricetape
    @property
    def qttytape(self):
        return self._qttytape
    @property
    def tstape(self):
        return self._tstape
    @property
    def lastTradePrice(self):
        return self._lastTradePrice
    @property
    def lastTradeSign(self):
        return self._lastTradeSign
    @property
    def name(self):
        return self._name
    @property
    def bids(self):
        return self._bids
    @property
    def asks(self):
        return self._asks
    @property
    def last_tick(self):
        return self._last_tick
    @property
    def last_timestamp(self):
        return self._last_timestamp
    @property
    def tick_size(self):
        return self._tick_size
    @property
    def next_order_id(self):
        self._next_order_id += 1
        return self._next_order_id
    @property
    def time(self):
        self._time = time.time_ns()
        return self._time

    @maxEntries.setter
    def maxEntries(self, maxEntries):
        self._maxEntries = maxEntries
    @LOBtape.setter
    def LOBtape(self, LOBtape):
        self._LOBtape = LOBtape
    @verbose.setter
    def verbose(self, verbose):
        self._verbose = verbose
    @pricetape.setter
    def pricetape(self, pricetape):
        self._pricetape = pricetape
    @qttytape.setter
    def qttytape(self, qttytape):
        self._qttytape = qttytape
    @tstape.setter
    def tstape(self, tstape):
        self._tstape = tstape
    @tick_size.setter
    def tick_size(self, tick_size):
        self._tick_size = Decimal(tick_size)
    @lastTradePrice.setter
    def lastTradePrice(self, lastTradePrice):
        self._lastTradePrice = lastTradePrice
    @lastTradeSign.setter
    def lastTradeSign(self, lastTradeSign):
        self._lastTradeSign = lastTradeSign
    @last_tick.setter
    def last_tick(self, last_tick):
        self._last_tick = last_tick
    @last_timestamp.setter
    def last_timestamp(self, last_timestamp):
        self._last_timestamp = last_timestamp
    @bids.setter
    def bids(self, bids):
        self._bids = bids
    @asks.setter
    def asks(self, asks):
        self._asks = asks
    @b_auction.setter
    def b_auction(self, b_auction):
        ######################################################
        # END OF AUCTION ALGORITHM
        # it means we went from auction to no auction. 
        # A price should be decided according to walras equilibrium : 
        # the price that maximizes the offer and demand
        ###############################################
        if self.b_auction and not b_auction:
            # find the best price and execute all orders
            bidPrices = pd.DataFrame([[price, self.bids.price_map[price].volume] for price in list(self.bids.prices)]).set_index(0)
            askPrices = pd.DataFrame([[price, self.asks.price_map[price].volume] for price in list(self.asks.prices)]).set_index(0)
            bidPrices.columns = ['bids']
            askPrices.columns = ['asks']

            # sort prices
            askPrices.sort_index(inplace=True)
            bidPrices.sort_index(ascending=False, inplace=False)

            # get cumulative volumes (cours C.A Lehalle)
            bidPrices['cum bids'] = bidPrices.loc[::-1, 'bids'].cumsum()[::-1]
            askPrices['cum asks'] = askPrices.cumsum()

            # Get the price that maximizes the exchanged volume.
            walras_df = pd.concat([bidPrices, askPrices], axis=1, sort=True).fillna(method='ffill').fillna(method='bfill')
            walras_df2 = walras_df[['cum bids', 'cum asks']].min(axis=1)[::-1]
            execPrice = walras_df2.idxmax()

            if self.verbose:
                print(f'\n*** END OF AUCTION ***\n Best price : {execPrice}')

            # We execute all bids > execPrice or asks < execPrice.
            self.process_order = self.process_order_during_continuous_trading
            old_b_tape_LOB = self.b_tape_LOB
            self._b_tape_LOB = False

            # First change the prices & re-order orders of the orderlist
            # according to timestamp
            # if not execPrice in self.bids.prices:
            #     self.bids.create_price(execPrice)
            # if not execPrice in self.asks.prices:
            #     self.asks.create_price(execPrice)
            for price in list(self.bids.prices):  
                if price > execPrice:
                    if self.verbose:
                        print(f'\n*** Removing bid price : {price}. Quantity : {self.bids.price_map[price].volume} ***')

                    # loop in orders of this order list, add them to the 
                    for order in self.bids.price_map[price]:    
                        order.price = execPrice
                        self.bids.move_order_with_time(order)
                        # execPrice_bid_orderlist.append_order_with_time(order)

                    self.bids.remove_price(price)
                    

            # print(self.asks.price_map[execPrice])
            for price in list(self.asks.prices):    
                if price < execPrice:
                    # loop in orders of this order list, add them to the 
                    if self.verbose:
                        print(f'\n*** Removing ask price : {price}. Quantity : {self.asks.price_map[price].volume} ***')
                    for order in self.asks.price_map[price]:    
                        order.price = execPrice
                        # update bids
                        self.asks.move_order_with_time(order)

                    self.asks.remove_price(price)

            
            execPrice_bid_orderlist = self.bids.price_map[execPrice]
            execPrice_ask_orderlist = self.asks.price_map[execPrice]

            if walras_df.loc[execPrice, 'cum asks']>walras_df.loc[execPrice, 'cum bids']: 
                #execute bids
                if self.verbose:
                    print(f'\n*** Executing all bids @{execPrice} ***')
                

                for order in execPrice_bid_orderlist:
                    quantity_to_trade, new_trades = self.process_order_list('ask', 
                                                                    execPrice_ask_orderlist, 
                                                                    order.quantity,
                                                                    {'order_id' : order.order_id,
                                                                     'trader_id': order.trader_id})
                self.bids.remove_price(execPrice)
            else:
                print(self.bids.price_map[execPrice])
                print(self.asks.price_map[execPrice])
                
                #execute asks
                if self.verbose:
                    print(f'\n*** Executing all asks @{execPrice} ***')
                for order in execPrice_ask_orderlist:
                    quantity_to_trade, new_trades = self.process_order_list('bid', 
                                                                    execPrice_bid_orderlist, 
                                                                    order.quantity,
                                                                    {'order_id' : order.order_id,
                                                                     'trader_id': order.trader_id})
                self.asks.remove_price(execPrice)
            self._b_tape_LOB = old_b_tape_LOB

        # it means we stop live trading, and all orders are just
        # added to the LOB without execution.
        # elif not self.b_auction and b_auction:
        self._b_auction = b_auction

        if self.b_auction:
            self.process_order = self.process_order_during_auction
        else:
            self.process_order = self.process_order_during_continuous_trading

    def addAgent(self, agent):
        self.agentList[agent.id] = agent

    def removeAgent(self, agent):
        del self.agentList[agent.id]

    def resetLOB(self):
        self._bids = OrderTree()
        self._asks = OrderTree()

    def reset(self):
        self.tape = deque(maxlen=None) 
        self.pricetape = []
        self.qttytape = []
        self.tstape = []
        self.bids = OrderTree()
        self.asks = OrderTree()

#########################################
# Order Processin Methods 
#########################################

    def notify_cancelation(self, side, trader_id, order_id):
        if trader_id in self.agentList:
            self.agentList[trader_id].notify_order_cancelation(side, order_id)

    def notify_modification(self, order_update):
        trader_id = order_update['trader_id']
        if trader_id in self.agentList:
            self.agentList[trader_id].notify_order_modification(order_update)

    def notify_agents(self, trades, order_in_book):
        if order_in_book:
            if order_in_book['trader_id'] in self.agentList:
                self.agentList[order_in_book['trader_id']].notify_orders_in_book(order_in_book)
        if trades:
            for trade in trades:
                if trade['party1_id'] in self.agentList:
                    self.agentList[trade['party1_id']].notify_trades(trade)
                elif trade['party2_id'] in self.agentList:
                    self.agentList[trade['party2_id']].notify_trades(trade, False)


    def process_order_during_auction(self, quote):
        order_type = quote['type']
        order_in_book = None
        quote['timestamp'] = self.time

        if quote['quantity'] <= 0:
            sys.exit('process_order() given order of quantity <= 0')

        # no market order during auctions
        if order_type == 'market':
            # Tape LOB state before processing order : 
            if self.b_tape_LOB:
                self.LOBtape.append(self.getCurrentLOB('market', 'MO', quote))
            
            if self.verbose:
                print(f'\n**** Error : **** \n: Market Order during auction mode {str(quote)}')

        elif order_type == 'limit':
            quote['price'] = Decimal(quote['price'])
            side = quote['side']

            # Tape LOB state before processing order : 
            if self.b_tape_LOB:
                self.LOBtape.append(self.getCurrentLOB('limit', 'LO', quote))
            
            if side=='bid':
                if not 'order_id' in quote:
                    quote['order_id'] = self.next_order_id
                self.bids.insert_order(quote)
                order_in_book = quote
            elif side=='ask':
                if not 'order_id' in quote:
                    quote['order_id'] = self.next_order_id
                self.asks.insert_order(quote)
                order_in_book = quote
            else:
                sys.exit('process_limit_order() given neither "bid" nor "ask"')
        else:
            sys.exit("order_type for process_order() is neither 'market' or 'limit'")
        
        self.notify_agents(None, order_in_book)
        return None, order_in_book

    def process_order_during_continuous_trading(self, quote):
        order_type = quote['type']
        order_in_book = None
        quote['timestamp'] = self.time

        if quote['quantity'] <= 0:
            sys.exit('process_order() given order of quantity <= 0')

        if order_type == 'market':

            # Tape LOB state before processing order : 
            if self.b_tape_LOB:
                self.LOBtape.append(self.getCurrentLOB('market', 'MO', quote))

            trades = self.process_market_order(quote)

        elif order_type == 'limit':
            quote['price'] = Decimal(quote['price'])

            # Tape LOB state before processing order : 
            if self.b_tape_LOB:
                self.LOBtape.append(self.getCurrentLOB('limit', 'LO', quote))

            trades, order_in_book = self.process_limit_order(quote)
        else:
            sys.exit("order_type for process_order() is neither 'market' or 'limit'")
        
        self.notify_agents(trades, order_in_book)
        return trades, order_in_book

    def process_order_list(self, side, order_list, quantity_still_to_trade, quote):
        '''
        Takes an OrderList (stack of orders at one price) and an incoming order and matches
        appropriate trades given the order's quantity.
        '''
        trades = []
        quantity_to_trade = quantity_still_to_trade
        while len(order_list) > 0 and quantity_to_trade > 0:
            head_order = order_list.get_head_order()
            traded_price = head_order.price
            counter_party = head_order.trader_id
            new_book_quantity = None
            if quantity_to_trade < head_order.quantity:
                traded_quantity = quantity_to_trade
                # Do the transaction
                new_book_quantity = head_order.quantity - quantity_to_trade
                head_order.update_quantity(new_book_quantity, head_order.timestamp)
                quantity_to_trade = 0
            elif quantity_to_trade == head_order.quantity:
                traded_quantity = quantity_to_trade
                if side == 'bid':
                    self.bids.remove_order_by_id(head_order.order_id)
                else:
                    self.asks.remove_order_by_id(head_order.order_id)
                quantity_to_trade = 0
            else: # quantity to trade is larger than the head order
                traded_quantity = head_order.quantity
                if side == 'bid':
                    self.bids.remove_order_by_id(head_order.order_id)
                else:
                    self.asks.remove_order_by_id(head_order.order_id)
                quantity_to_trade -= traded_quantity

            transaction_record = {
                    # 'timestamp': self.time,
                    'traded_price': traded_price,
                    'traded_quantity': traded_quantity,
                    'time': self.time
                    }

            party2_orderid=quote['order_id'] if 'order_id' in quote else None 

            if side == 'bid':  
                transaction_record['party1_id'] = counter_party
                transaction_record['party1_side'] = 'bid'
                transaction_record['party1_order_id'] = head_order.order_id

                # transaction_record['party1_newbookquantity'] = [counter_party, 'bid', head_order.order_id, new_book_quantity]
                transaction_record['party2_id'] = quote['trader_id']
                transaction_record['party2_side'] = 'ask'
                transaction_record['party2_order_id'] = party2_orderid # None means that the sender of order is party 2
                self.lastTradeSign = 'ask'
            else:
                transaction_record['party1_id'] = counter_party
                transaction_record['party1_side'] = 'ask'
                transaction_record['party1_order_id'] = head_order.order_id

                transaction_record['party2_id'] = quote['trader_id']
                transaction_record['party2_side'] = 'ask'
                transaction_record['party2_order_id'] = party2_orderid # None means that the sender of order is party 2
                self.lastTradeSign = 'bid'

            if self.verbose:
                print(f'\n**** New Trade : **** \n: {str(transaction_record)}')

            self.lastTradePrice = traded_price      
            if self.b_tape:           
                self.tape.append(transaction_record)

                #FDR
                self.tstape    += [self.time]
                self.pricetape += [traded_price]
                self.qttytape  += [traded_quantity]
                
                trades.append(transaction_record)

        return quantity_to_trade, trades
    
    def process_market_order(self, quote):
        if self.verbose:
            print(f'\n**** I received this market order **** \n: {str(quote)}')

        trades = []
        quantity_to_trade = quote['quantity']
        side = quote['side']
        if side == 'bid':
            while quantity_to_trade > 0 and self.asks:
                best_price_asks = self.asks.min_price_list()
                quantity_to_trade, new_trades = self.process_order_list('ask', best_price_asks, quantity_to_trade, quote)
                trades += new_trades
        elif side == 'ask':
            while quantity_to_trade > 0 and self.bids:
                best_price_bids = self.bids.max_price_list()
                quantity_to_trade, new_trades = self.process_order_list('bid', best_price_bids, quantity_to_trade, quote)
                trades += new_trades
        else:
            sys.exit('process_market_order() recieved neither "bid" nor "ask"')
        return trades

    def process_limit_order(self, quote):
        if self.verbose:
            print(f'\n**** I received this limit order **** \n: {str(quote)}')

        order_in_book = None
        trades = []
        quantity_to_trade = quote['quantity']
        side = quote['side']
        price = quote['price']
        if side == 'bid':
            while (self.asks and price >= self.asks.min_price() and quantity_to_trade > 0):
                best_price_asks = self.asks.min_price_list()
                quantity_to_trade, new_trades = self.process_order_list('ask', best_price_asks, quantity_to_trade, quote)
                trades += new_trades
            # If volume remains, need to update the book with new quantity
            if quantity_to_trade > 0:
                if not 'order_id' in quote:
                    quote['order_id'] = self.next_order_id
                quote['quantity'] = quantity_to_trade
                self.bids.insert_order(quote)
                order_in_book = quote
        elif side == 'ask':
            while (self.bids and price <= self.bids.max_price() and quantity_to_trade > 0):
                best_price_bids = self.bids.max_price_list()
                quantity_to_trade, new_trades = self.process_order_list('bid', best_price_bids, quantity_to_trade, quote)
                trades += new_trades
            # If volume remains, need to update the book with new quantity
            if quantity_to_trade > 0:
                if not 'order_id' in quote:
                    quote['order_id'] = self.next_order_id
                quote['quantity'] = quantity_to_trade
                self.asks.insert_order(quote)
                order_in_book = quote
        else:
            sys.exit('process_limit_order() given neither "bid" nor "ask"')
        return trades, order_in_book

    def cancel_order(self, side, order_id):
        if self.verbose:
            print(f'\n**** I received this cancel order **** \n: {str(order_id)}')

        # Tape LOB state before processing order : 
        self.cancel_order_tape(side, order_id)

        # Cancel Order
        trader_id = None
        if side == 'bid':
            if self.bids.order_exists(order_id):
                trader_id = self.bids.remove_order_by_id(order_id)
            else:
                if self.verbose:
                    print(f'\n**** Cancel Error : Order does not exist **** \n: {str(order_id)}')

        elif side == 'ask':
            if self.asks.order_exists(order_id):
                trader_id = self.asks.remove_order_by_id(order_id)
            else:
                if self.verbose:
                    print(f'\n**** Cancel Error : Order does not exist **** \n: {str(order_id)}')

        else:
            sys.exit('cancel_order() given neither "bid" nor "ask"')
        
        if trader_id:
            self.notify_cancelation(side, trader_id, order_id)

    # add the cancel order to the tape
    def cancel_order_tape(self, side, order_id):
        if self.b_tape_LOB:
            if side == 'bid':
                if self.bids.order_exists(order_id):
                    order = self.bids.order_map[order_id]
                    self.LOBtape.append(self.getCurrentLOB('limit', 'cancel', order))
                else:
                    self.LOBtape.append(self.getCurrentLOB('limit', 'cancel', {'order_id':order_id}))
            elif side == 'ask':
                if self.asks.order_exists(order_id):
                    order = self.asks.order_map[order_id]
                    self.LOBtape.append(self.getCurrentLOB('limit', 'cancel', order))
                else:
                    self.LOBtape.append(self.getCurrentLOB('limit', 'cancel', {'order_id':order_id}))
            else:
                sys.exit('cancel_order() given neither "bid" nor "ask"')
    
    ######################################################################
    # Order cancelation rules :
    # 4202/4 Modification and cancellation.
    # Any order entered into the Central Order Book may be modified or 
    # cancelled prior to its execution. Any increase in the order  
    # quantity or change in the limit price shall cause the forfeiture 
    # of time priority.
    ######################################################################
    
    def modify_order(self, order_id, order_update):
        if self.verbose:
            print(f'\n**** I received this modify order **** \n: {str(order_id)} : {str(order_update)}')

        side = order_update['side']
        order_update['order_id'] = order_id
        order_update['timestamp'] = self.time

        # Tape LOB state before processing order : 
        if self.b_tape_LOB:
            self.LOBtape.append(self.getCurrentLOB('limit', 'modify', order_update))

        if side == 'bid':
            if self.bids.order_exists(order_update['order_id']):
                # Check if the order looses priority :
                if self.bids.update_order_looses_priority(order_update):
                    # if true, delete order and re process it (if it becomes agressive)
                    trader_id = self.bids.remove_order_by_id(order_id)
                    
                    # don't record the new order, it isn't new.
                    old_b_tape_lob = self.b_tape_LOB
                    self._b_tape_LOB = False
                    self.process_order(order_update)
                    self._b_tape_LOB = old_b_tape_lob
                    
                else:
                    self.bids.update_order_quantity(order_update)
                    self.notify_modification(order_update)
            else:
                if self.verbose:
                    print(f'\n**** Order modification Error : order does not exist **** \n: {str(order_id)}')
        
        elif side == 'ask':
            if self.asks.order_exists(order_update['order_id']):
                # Check if the order looses priority :
                if self.asks.update_order_looses_priority(order_update):
                    # if true, delete order and re process it (if it becomes agressive)
                    trader_id = self.asks.remove_order_by_id(order_id)

                    # don't record the new order, it isn't new.
                    old_b_tape_lob = self.b_tape_LOB
                    self._b_tape_LOB = False
                    self.process_order(order_update)
                    self._b_tape_LOB = old_b_tape_lob
                else:
                    self.asks.update_order_quantity(order_update)
                    self.notify_modification(order_update)
            else:
                if self.verbose:
                    print(f'\n**** Order modification Error : order does not exist **** \n: {str(order_id)}')
        else:
            sys.exit('modify_order() given neither "bid" nor "ask"')


    def modify_order_old(self, order_id, order_update):
        if self.verbose:
            print(f'\n**** I received this modify order **** \n: {str(order_id)}')
                
        side = order_update['side']
        order_update['order_id'] = order_id
        order_update['timestamp'] = self.time

        # Tape LOB state before processing order : 
        if self.b_tape_LOB:
            self.LOBtape.append(self.getCurrentLOB('limit', 'modify', order_update))

        if side == 'bid':
            if self.bids.order_exists(order_update['order_id']):
                self.bids.update_order(order_update)

                # self.notify_modification(order_id, order_update)
            else:
                if self.verbose:
                    print(f'\n**** Order modification Error : order does not exist **** \n: {str(order_id)}')
        elif side == 'ask':
            if self.asks.order_exists(order_update['order_id']):
                self.asks.update_order(order_update)
            else:
                if self.verbose:
                    print(f'\n**** Order modification Error : order does not exist **** \n: {str(order_id)}')
        else:
            sys.exit('modify_order() given neither "bid" nor "ask"')

#########################################
# Order Book state information 
#########################################
    def get_volume_at_price(self, side, price):
        price = Decimal(price)
        if side == 'bid':
            volume = 0
            if self.bids.price_exists(price):
                volume = self.bids.get_price_list(price).volume
            return volume
        elif side == 'ask':
            volume = 0
            if self.asks.price_exists(price):
                volume = self.asks.get_price_list(price).volume
            return volume
        else:
            sys.exit('get_volume_at_price() given neither "bid" nor "ask"')

    def get_best_bid(self):
        return self.bids.max_price()

    def get_worst_bid(self):
        return self.bids.min_price()

    def get_best_ask(self):
        return self.asks.min_price()

    def get_worst_ask(self):
        return self.asks.max_price()

#########################################
# Order Book Purging
#########################################
    def tape_dump(self, filename, filemode, tapemode):
        if filename is not None:
            dumpfile = open(filename, filemode)
            for tapeitem in self.tape:
                dumpfile.write('Time: %s, Price: %s, Quantity: %s\n' % (tapeitem['time'],
                                                                        tapeitem['price'],
                                                                        tapeitem['quantity']))
            dumpfile.close()
        if tapemode == 'wipe':
            self.tape = []


#########################################
# Order Book Statistical info : volatility ? imbalance ?  
#########################################

        


        
#########################################
# Fancy Outputs
#########################################
    def getCurrentLOB(self, ordertype_, actiontype_, order, side=None):
        # gives the -i best bids & i asks and corersponding quantities as a dictionary
        # bids:
        if type(order) == dict:
            order_id = order['order_id'] if 'order_id' in order else None
            timestamp = order['timestamp'] if 'timestamp' in order else None
            price = order['price'] if 'price' in order else None
            quantity = order['quantity'] if 'quantity' in order else None
            side = order['side'] if 'side' in order else None
        else:
            order_id = order.order_id
            timestamp = order.timestamp
            price = order.price
            quantity = order.quantity
            side = order.side

        res = [timestamp,  order_id,  price,  quantity,  side,  ordertype_, actiontype_]
        res += [0, 0, 0, 0] * self.maxEntries
        
        # if it is auction mode, don't store limits
        if not self.b_auction:
            j = 7+2*self.maxEntries-1
            try:
                bestbid = self.bids.prices[-1]

                for i in range(self.maxEntries):
                    price = bestbid - i*self.tick_size
                    res[j-1] = price
                    res[j] = self.bids.price_map[price].volume if price in self.bids.prices else 0
                    j -= 2
            except:
                if len(self.bids.prices) > 0:
                    sys.exit('ERROR !')    
            

            j = 7+2*self.maxEntries
            try:
                bestask = self.asks.prices[0]

                for i in range(self.maxEntries):
                    price = bestask + i*self.tick_size
                    res[j] = price
                    res[j+1] = self.asks.price_map[price].volume if price in self.asks.prices else 0
                    j += 2
            except:
                if len(self.asks.prices) > 0:
                    sys.exit('ERROR !')
            
        return res


    def getLOBstate(self):
        resDF = pd.DataFrame([0])
        for _, value in self.bids.price_map.items():
            for order_ in value:
                px = float(order_.price)
                qtty = float(order_.quantity)
                
                if not px in resDF.index:
                    resDF.loc[px] = -qtty
                else:
                    resDF.loc[px] -= qtty
        
        for _, value in self.asks.price_map.items():
            for order_ in value:
                px = float(order_.price)
                qtty = float(order_.quantity)
                
                if not px in resDF.index:
                    resDF.loc[px] = qtty
                else:
                    resDF.loc[px] += qtty
        resDF.drop(resDF.index[0], inplace=True)
        resDF.reset_index(inplace=True)
        resDF.columns = ['Price', 'Quantity']
        return resDF

    def to_png(self, _cache={}):
        # create a dataframe with bis & asks
        # bids are positive quantities, asks are negative.
        import pandas as pd
        import matplotlib.pyplot as plt

        resDF = pd.DataFrame([np.nan])
        for _, value in self.bids.price_map.items():
            for order_ in value:
                px = float(order_.price)
                qtty = float(order_.quantity)
                
                if not px in resDF.index:
                    resDF.loc[px] = qtty
                else:
                    resDF.loc[px] += qtty
        
        for _, value in self.asks.price_map.items():
            for order_ in value:
                px = float(order_.price)
                qtty = float(order_.quantity)
                
                if not px in resDF.index:
                    resDF.loc[px] = -qtty
                else:
                    resDF.loc[px] -= qtty

        resDF =  resDF.sort_index().dropna()
        fig, (ax1, ax2, ax3) = plt.subplots(3, 1, figsize=(15, 8))
        resDF.columns = ['Quantites']
        resDF.plot.bar(rot=0, ax=ax1)

        # Prices
        if self.tape != None and len(self.tape) > 0:
            ax2.plot(self.tstape, self.pricetape)
            ax3.bar(self.tstape, self.qttytape)
            
        # save fig
        fig.savefig(r'static/LOB.png')
        plt.close()
        return 'DONE'

    def to_html(self):
        tempfile = ''
        tempfile += '***Bids***<br />'
        if self.bids != None and len(self.bids) > 0:
            for key, value in reversed(self.bids.price_map.items()):
                tempfile += f'{value}<br />'
        tempfile += "<br />***Asks***<br />"
        if self.asks != None and len(self.asks) > 0:
            for key, value in self.asks.price_map.items():
                tempfile += f'{value}<br />'
        return tempfile
    
    def __str__(self):
        # return self.name

        tempfile = StringIO()
        tempfile.write("***Bids***\n")
        if self.bids != None and len(self.bids) > 0:
            for key, value in reversed(self.bids.price_map.items()):
                tempfile.write('%s' % value)
        tempfile.write("\n***Asks***\n")
        if self.asks != None and len(self.asks) > 0:
            for key, value in self.asks.price_map.items():
                tempfile.write('%s' % value)
        tempfile.write("\n***Trades***\n")
        if self.tape != None and len(self.tape) > 0:
            num = 0
            for entry in self.tape:
                if num < 10: # get last 5 entries
                    tempfile.write(str(entry['quantity']) + " @ " + str(entry['price']) + " (" + str(entry['timestamp']) + ") " + str(entry['party1'][0]) + "/" + str(entry['party2'][0]) + "\n")
                    num += 1
                else:
                    break
        tempfile.write("\n")
        return tempfile.getvalue()

