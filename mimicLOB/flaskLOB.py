from flask import Flask, render_template, request, Response
from orderbook.orderbook import OrderBook
from agent.randomAgent import randomAgent
from agent.basicMarketMaker import basicMarketMaker
from pprint import pprint, pformat
import datetime
from apscheduler.schedulers.background import BackgroundScheduler
import time
import json

# Create an order book
sched = BackgroundScheduler()
order_book = OrderBook()
order_book.scheduler = sched
order_book.tick_size = 1
first_price = 1000

class bl():
    def __init__(self):
        self.paused = False
paused = bl()




# Create the Flask app
app = Flask(__name__)
 
def launchSimulation():
    #sched.add_job(updateGraphs, 'interval', seconds=5)
    try:
        sched.start()

        # Create a market maker
        MM = basicMarketMaker(order_book)

        # Create some buyers
        buyer1 = randomAgent(order_book, type_ = 'randomLimitBuyer')
        buyer2 = randomAgent(order_book, type_ = 'randomMarketBuyer')

        # Create some buyers
        seller1 = randomAgent(order_book, type_ = 'randomLimitSeller')
        seller2 = randomAgent(order_book, type_ = 'randomMarketSeller')
        
        # seconds can be replaced with minutes, hours, or days
        MM.act()
        buyer1.act()     
        buyer2.act()     
        seller1.act()   
        seller2.act()
    except:
        for job in sched.get_jobs():
            print(job)
            job.resume()

        # sched.resume()
    paused.paused = False
    return None
    
def stopSimulation():
    # Launch a thread launching buy orders
    order_book.tape_dump(None, None, 'wipe')
    for job in sched.get_jobs():
        job.pause()
        # sched.resume()
    paused.paused = True
# def updateGraphs():
#     # generate the png
#     order_book.to_png()



@app.route('/chart-data')
def chart_data():
    if not paused.paused :
        def plotLivePrices():
            import random
            import time
            from datetime import datetime
            random.seed()  # Initialize the random number generator
            while True:
                json_data = json.dumps(
                    {'time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'), 'value': float(order_book.get_best_bid())})
                yield f"data:{json_data}\n\n"
                time.sleep(0.2)

            
        return Response(plotLivePrices(), mimetype='text/event-stream')
    else:
        return None

@app.route('/', methods=['GET', 'POST'])
def index():
    global i
    if 'Start' in request.form:
        i = 0
        launchSimulation() # do something
    elif 'Stop' in request.form:
        stopSimulation() 

    return render_template("index.html")

    
@app.route("/liveLOB")
def liveLOB():
    return render_template("liveLOB.html", LiveLOB=order_book.to_html())

@app.route('/Interact', methods=['GET', 'POST'])
def Interact():

    # An agent is sending a request

    # If he's trying to 
    
    # get an image of the order book
    return 0


if __name__ == "__main__":
    app.run(debug=True)