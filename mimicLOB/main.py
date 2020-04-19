from flask import Flask, render_template, request, Response, jsonify
from orderbook.orderbook import OrderBook
from internalAgent.randomAgent import randomAgent
from internalAgent.basicMarketMaker import basicMarketMaker
from information.channel import Channel
from pprint import pprint, pformat
from decimal import Decimal
import datetime
# from apscheduler.schedulers.background import BackgroundScheduler
import time
import json
import importlib
import pandas as pd
# import socketio
# 
# create a Socket.IO server
# sio = socketio.Server()

#################################################################
# logs
#################################################################
import sys
# open(r'static/logs/mainLog.txt', 'w').close()
# sys.stdout = open(r'tmp/mainLog.txt', 'w')

#################################################################
# Global variables for the simulator
#################################################################
# sched = BackgroundScheduler()
order_book = OrderBook(distant=True,
                       tick_size = Decimal(1),
                       b_tape = True,
                       b_tape_LOB = False,
                       verbose = True)
# order_book.scheduler = sched
agentFactory = {} # keeps references on agents
newsFactory = {} # keeps references on informations
# sched.start()
newsChannel = Channel()
#################################################################

#################################################################
# Pausing system
#################################################################
class bl():
    def __init__(self):
        self.paused = False
paused = bl()
#################################################################

#################################################################
# Configuration of the simulator
#################################################################
# global SimulatorConfiguration
# import simulationConfigs.randomConfig as configModule
# SimulatorConfiguration = configModule.get_config(order_book=order_book,
#                                                  sched = sched,
#                                                  newsChannel = newsChannel)


def getInstance(module, defObject, **kwargs):
    typ = defObject['type']
    exec(f'global myModule; from {module} import {typ} as myModule')
    class_ = getattr(myModule, typ)
    return class_(**defObject)

# Create the Flask app
app = Flask(__name__)
 
# def launchNews():
#     #############################
#     # configs
#     #############################
#     config_news = SimulatorConfiguration['information']

#     #############################
#     # Information
#     #############################
#     for info in config_news:
#         newsFactory[info] = getInstance('information', config_news[info])

#     #############################
#     # Start Actions
#     #############################
#     for news in newsFactory:
#         newsFactory[news].act()
    
#     return None

# def launchAgents():
#     #############################
#     # configs
#     #############################
#     config_agents = SimulatorConfiguration['agents']

#     #############################
#     # Agents
#     #############################
#     for agent in config_agents:
#         agentFactory[agent] = getInstance('internalAgent', config_agents[agent])        

#     #############################
#     # Start Actions
#     #############################
#     # First agents
#     for agent in agentFactory:
#         agentFactory[agent].act()

#     paused.paused = False
#     return None


# def stopAgents():
#     # Agents stops their jobs
#     for agent in agentFactory:
#         agentFactory[agent].stop()
#     paused.paused = True

# def stopNews():
#     # Info generators stops their jobs
#     for news in newsFactory:
#         newsFactory[news].stop()
    



####################################################
###############################################
# SERVER APP ROUTES
###############################################
####################################################
@app.route("/liveLOB")
def liveLOB():
    return render_template("liveLOB.html", LiveLOB=order_book.to_html())

@app.route("/histoLOB")
def histoLOB():
    return render_template("histoLOB.html")

@app.route("/Logs")
def Logs():
    sys.stdout.flush()
    return render_template("Logs.html")

@app.route('/chart-NEWS')
def chart_news():
    if not paused.paused :
        def plotLiveNews():
            from datetime import datetime
            while True:
                json_data = json.dumps(
                    {'time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'), 'value': newsChannel.get_latest_news().val})
                yield f"data:{json_data}\n\n"
                time.sleep(1)

        return Response(plotLiveNews(), mimetype='text/event-stream')
    else:
        return None

@app.route('/chart-pricesBID')
def chart_prices_bid():
    if not paused.paused :
        def plotLivePrices():
            from datetime import datetime
            while True:
                try:
                    json_data = json.dumps(
                        {'time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'), 'value': float(order_book.get_best_bid())})
                    yield f"data:{json_data}\n\n"
                    
                except Exception as e:
                    json_data = json.dumps(
                        {'time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'), 'value': 10})
                    yield f"data:{json_data}\n\n"
                    print(f'ERROR while updating the bid prices, probably no best ask in LOB : {str(e)}')
                time.sleep(1)
        return Response(plotLivePrices(), mimetype='text/event-stream')
    else:
        return None

@app.route('/chart-pricesASK')
def chart_prices_ask():
    if not paused.paused :
        def plotLivePrices():
            from datetime import datetime
            while True:
                try:
                    json_data = json.dumps(
                        {'time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'), 'value': float(order_book.get_best_ask())})
                    yield f"data:{json_data}\n\n"
                    
                except Exception as e:
                    json_data = json.dumps(
                        {'time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'), 'value': 11})
                    yield f"data:{json_data}\n\n"
                    print(f'ERROR while updating the ask prices, probably no best ask in LOB : {str(e)}')
                time.sleep(1)
        return Response(plotLivePrices(), mimetype='text/event-stream')
    else:
        return None

@app.route('/chart-histo')
def chart_histo():
    # this one runs even if the simulation stops
    def plotHistoPrices():
        prices = order_book.pricetape
        while True:
            try:
                json_data = json.dumps(
                    {'times': [i for i in range(len(prices))], 'value': [float(p) for p in prices]})                
                yield f"data:{json_data}\n\n"
                
            except Exception as e:
                print(f'ERROR while updating the historical prices, probably no transactions : {str(e)}')
            time.sleep(3)
    return Response(plotHistoPrices(), mimetype='text/event-stream')

@app.route('/chart-qtties')
def chart_qtties():
    if not paused.paused :
        def plotLivePrices():
            from datetime import datetime
            while True:
                try:
                    json_data = json.dumps(
                        {'time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'), 'value': float(order_book.qttytape[-1])})
                    yield f"data:{json_data}\n\n"
                except Exception as e:
                    print(f'ERROR while updating quantity bars : {str(e)}')
                time.sleep(1)

        return Response(plotLivePrices(), mimetype='text/event-stream')
    else:
        return None

@app.route('/chart-LOB')
def chart_LOB():
    if not paused.paused :
        def plotLiveLOB():
            while True:
                try:
                    LOBstate = order_book.getLOBstate() 
                    # print('HHHHHHHHHHHHHHAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAHHHHHHHHHHHHHHHHHHHHHHHH')
                    # print(LOBstate)
                    
                    # print({'prices': list(LOBstate.index), 'quantities':list(LOBstate.iloc[:,0].values)})
                    json_data = json.dumps(
                        {'prices': list(LOBstate.Price), 'quantities':list(LOBstate.Quantity)})
                    yield f"data:{json_data}\n\n"   
                except Exception as e:
                    print(f'ERROR while updating live LOB graph : {str(e)}')
                time.sleep(1)

        return Response(plotLiveLOB(), mimetype='text/event-stream')
    else:
        return None

@app.route('/', methods=['GET', 'POST'])
def index():
    global i
    # from random import randint, randrange
    # if 'Start' in request.form:
    #     i = 0
    #     launchNews()
    #     launchAgents()
    # elif 'Stop' in request.form:
    #     stopAgents()
    #     stopNews()
    return render_template("index.html")
    # return render_template("index.html", ConfigurationAddress = hex(id(SimulatorConfiguration)),
    #                                      LOBAddress = hex(id(order_book)),                                         
    #                                      AgentConfiguration=pd.DataFrame(data=SimulatorConfiguration['agents']).T.fillna("").to_html(),
    #                                      NewsConfiguration=pd.DataFrame(data=SimulatorConfiguration['information']).T.fillna("").to_html())

####################################################
###############################################
# Accessors to LOB 
###############################################
####################################################
@app.route('/getTransactionTape')
def getgetTransactionTape():
    TransactionTape = pd.DataFrame({i: [tapeitem['time'],
                                        tapeitem['party1_id'], 
                                        tapeitem['party1_side'], 
                                        tapeitem['party1_order_id'], 
                                        tapeitem['party2_id'], 
                                        tapeitem['party1_side'],
                                        tapeitem['party2_order_id'],
                                        tapeitem['traded_price'], 
                                        tapeitem['traded_quantity']] for (i, tapeitem) in enumerate(order_book.tape)}).T
    if len(TransactionTape)>0:
        TransactionTape.columns = ['time', 'party1_id', 'party1_side', 'party1_order_id', 
                                    'party2_id', 'party2_side', 'party2_order_id',
                                    'traded_price', 'traded_quantity']
        return jsonify({'TransactionTape' : TransactionTape.to_json()})
    else:
        return jsonify({'status': 'No transactions'})

@app.route('/getPriceTape')
def getPriceTape():
    return jsonify({'PriceTape' : order_book.pricetape})

@app.route('/getLOBstate')
def getLOBstate():
    return jsonify({'LOBstate' : order_book.getLOBstate().to_json() })

@app.route('/getbestbid')
def getbestbid():
    return jsonify({'bestbid' : order_book.get_best_bid()})

@app.route('/getbestask')
def getbestask():
    return jsonify({'bestask' : order_book.get_best_ask()})

@app.route('/setticksize')
def setticksize():
    ticksize= request.get_json()['ticksize']
    order_book.tick_size = ticksize
    return jsonify({'status' : 'DONE'})

@app.route('/getticksize')
def getticksize():
    return jsonify({'ticksize' : order_book.tick_size})

@app.route('/getlastTradePrice')
def getlastTradePrice():
    return jsonify({'lastTradePrice' : order_book.lastTradePrice})

@app.route('/getlastTradeSign')
def getlastTradeSign():
    return jsonify({'lastTradeSign' : order_book.lastTradeSign})

@app.route('/getlastnews')
def getlastnews():
    return jsonify({'lastnews' : newsChannel.get_latest_news().val})

@app.route('/cancelOrder')
def cancelOrder():
    params= request.get_json()
    side = params['side']
    id_ = params['id']
    order_book.cancel_order(side, id_)
    return jsonify({'status': 'CANCELED'})

@app.route('/get_volume_at_price')
def get_volume_at_price():
    params= request.get_json()
    side = params['side']
    price = params['price']
    result = order_book.get_volume_at_price(side, price)
    return jsonify({'volume': result})

@app.route('/sendOrder')
def sendOrder():
    order = request.get_json()
    trades, pendingOrders = order_book.process_order(order)
    return jsonify({'status': 'SENT', 
                    'trades' : trades, 
                    'pendingOrders':pendingOrders})

@app.route('/modifyOrder')
def modifyOrder():
    params = request.get_json()
    order = params['order']
    order_id = params['order_id'] 

    order_book.modify_order(order_id, order)
    
    return jsonify({'status': 'ORDER MODIFIED'})

@app.route("/reset")
def reset():
    order_book.reset()
    return jsonify({'status': 'DONE'})

@app.route("/resetLOB")
def resetLOB():
    order_book.resetLOB()
    return jsonify({'status': 'DONE'})

@app.route("/launchNews")
def launchNews_():
    launchNews()
    return jsonify({'status': 'DONE'})

@app.route("/stopNews")
def stopNews_():
    stopNews()
    return jsonify({'status': 'DONE'})

@app.route("/addAgent2LOB")
def addAgent2LOB():
    params = request.get_json()
    order_book.addAgent(params)
    return jsonify({'status': 'DONE'})

@app.route('/Interact', methods=['GET', 'POST'])
def Interact():

    # An agent is sending a request

    # If he's trying to 
    
    # get an image of the order book
    return 0


if __name__ == "__main__":
    app.run(debug=True, port=sys.argv[1])
