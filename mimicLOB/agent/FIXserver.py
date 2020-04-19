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


class FIXserver:
    def __init__(self, agent, port):
        # self.LOBserver = LOBserver
        self.agent = agent

        # Create the Flask app
        app = Flask(__name__)
        self.app = app

        # launch the flask app
        @self.app.route('/notify_order_modification')
        def notify_order_modification():
            order_update = request.get_json()
            agent.notify_order_modification(order_update)
            return jsonify({'Status' : "DONE"})           

        @self.app.route('/notify_order_cancelation')
        def notify_order_cancelation():
            params = request.get_json()
            side = params['side']
            order_id = params['order_id']            
            agent.notify_order_cancelation(side, order_id)
            return jsonify({'Status' : "DONE"})
        
        @self.app.route('/notify_orders_in_book')
        def notify_orders_in_book():
            pendingOrder = request.get_json()
            agent.notify_orders_in_book(pendingOrder)
            return jsonify({'Status' : "DONE"})

        @self.app.route('/notify_trades')
        def notify_trades():
            params = request.get_json()
            trade = params['trade']
            check_pending = params['check_pending']
            agent.notify_trades(trade, check_pending)
            return jsonify({'Status' : "DONE"})
        
        self.app.run(debug=True, port=port)

    def getAddress(self):
        return self.app.root_path
#     app.run(debug=True, port=sys.argv[1])
