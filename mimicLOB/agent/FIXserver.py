# -*- coding: utf-8 -*-
"""
Created on Thu Apr 12 19:01:34 2018

This is a FIX ENGINE inspired class .

If the setup uis CLient / Server, each agent runs its internal 
flask server to receive fills & other FIX messages from 
the LOBs.

@author: FDR
"""

""" 
Imports
"""
from flask import Flask, render_template, request, Response, jsonify
import sys
from sortedcontainers import SortedDict

app = Flask(__name__)

# distant containers for the gent
class internalAgentData():
    def __init__(self):
        self.pendingorders = SortedDict()
        self.executedtrades = SortedDict()
        self.sentorders = SortedDict()
        self.id_ = ''
        self._i_trades = -1
        self._i_orders = -1


    @property
    def i_orders(self):
        self._i_orders += 1
        return self._i_orders
    @property
    def i_trades(self):
        self._i_trades += 1
        return self._i_trades
            
agentData = internalAgentData()

# launch the flask app
@app.route('/pendingorders')
def pendingorders():
    return jsonify({'pendingorders' : agentData.pendingorders})   

@app.route('/executedtrades')
def executedtrades():
    return jsonify({'executedtrades' : agentData.executedtrades})   

@app.route('/sentorders')
def sentorders():
    return jsonify({'sentorders' : agentData.sentorders})   

@app.route('/addSentOrders')
def addSentOrders():
    order = request.get_json()
    if order:
        agentData.sentorders[agentData.i_orders] = order
    return jsonify({'Status' : "DONE"})   

@app.route('/setid')
def setid():
    agentData.id_ = request.get_json()['id']
    return jsonify({'Status' : "DONE"})   

@app.route('/notify_order_modification')
def notify_order_modification():
    order_update = request.get_json()

    if order_update:
        agentData.pendingorders[order_update['order_id']]['quantity'] = order_update['quantity']

    return jsonify({'Status' : "DONE"})           

@app.route('/notify_order_cancelation')
def notify_order_cancelation():
    params = request.get_json()
    side = params['side']
    order_id = params['order_id']            
    
    if order_id:
        if order_id in agentData.pendingorders:
            del agentData.pendingorders[order_id]

        # add cancelation to sent orders
        agentData.sentorders[agentData.i_orders] = {'type'      : 'cancel', 
                                                    'side'      : side,
                                                    'trader_id' : agentData.id_,
                                                    'order_id'  : order_id}
                        
    return jsonify({'Status' : "DONE"})

@app.route('/notify_orders_in_book')
def notify_orders_in_book():
    pendingOrder = request.get_json()
    if pendingOrder is not None:
            agentData.pendingorders[pendingOrder['order_id']] = pendingOrder
        
    return jsonify({'Status' : "DONE"})

@app.route('/notify_trades')
def notify_trades():
    params = request.get_json()
    trade = params['trade']
    check_pending = params['check_pending']
    
    if trade:
        agentData.executedtrades[agentData.i_trades] = trade
        
        # update pending orders : if a trade fills a pending order
        # it must be deleted from pendingOrders, otherwise, the
        # quantity must be reduced
        if trade['party1_id'] == agentData.id_:
            order_id = trade['party1_order_id']
        elif trade['party2_id'] == agentData.id_:
            order_id = trade['party2_order_id']
        else:
            sys.exit(f'Fatal Error : Notify for agent {agentData.id_}')
        
        # if false, it means it is trades that has been executed
        # directly after sending (agressive limit order or market order)
        if check_pending:
            traded_quantity = trade['traded_quantity']
            
            agentData.pendingorders[order_id]['quantity'] -= traded_quantity
            
            if agentData.pendingorders[order_id]['quantity'] == 0: 
                del agentData.pendingorders[order_id]

            elif agentData.pendingorders[order_id]['quantity'] < 0: 
                sys.exit(f'Fatal Error 2 : Notify for agent {agentData.id_}')

    return jsonify({'Status' : "DONE"})


if __name__ == "__main__":
    app.run(debug=True, port=sys.argv[1])
