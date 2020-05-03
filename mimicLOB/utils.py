import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
def getInstance(module, defObject, **kwargs):
    typ = defObject['type']
    exec(f'global myModule; from {module} import {typ} as myModule')
    class_ = getattr(myModule, typ)
    return class_(**defObject)

def getBookHistory(executedTrades, id_):
    executedTrades['value'] = executedTrades['traded_price'] * executedTrades['traded_quantity']
    book_bids = executedTrades[['time', 'value']]
    book_bids.value= 0
    book_asks = book_bids.copy()
 
    bids1 = executedTrades[((executedTrades.party1_id==id_) & (executedTrades.party1_side == 'bid'))].value 
    bids2 = executedTrades[((executedTrades.party2_id==id_) & (executedTrades.party2_side == 'bid'))].value
    asks1 = executedTrades[((executedTrades.party1_id==id_) & (executedTrades.party1_side == 'ask'))].value
    asks2 = executedTrades[((executedTrades.party2_id==id_) & (executedTrades.party2_side == 'ask'))].value
    
    book_bids.loc[bids1.index, 'value'] += bids1
    book_bids.loc[bids2.index, 'value'] += bids2
    book_asks.loc[asks1.index, 'value'] += asks1
    book_asks.loc[asks1.index, 'value'] += asks2
    
    
    book_bids = book_bids.groupby('time').sum().cumsum()
    book_asks = book_asks.groupby('time').sum().cumsum()
    book = pd.concat([book_bids, book_asks], axis=1).fillna(method='ffill')
    book['all'] = book.iloc[:, 1] - book.iloc[:, 0] 
    book.columns = ['bids', 'asks', 'all']
    return book 

class LivePlotNotebook(object):
    """
    Live plot using %matplotlib notebook in jupyter notebook
    
    Usage:
    ```
    import time
    liveplot = LivePlotNotebook()
    x=np.random.random((10,))
    for i in range(10):
        time.sleep(1)
        liveplot.update(
            x=x+np.random.random(x.shape)/10,
            actions=np.random.randint(0, 3, size=(10,))
        )
    ```
    
    url:
    """

    def __init__(self):
        
        fig,(ax, ax2) = plt.subplots(1,2, constrained_layout=True)
#         fig.canvas.layout.width = '500px'
        
#         fig.canvas
        
        ax.plot([0]*20, label='best bid')
        ax.plot([0]*20, label='best ask')        
        ax.plot([1]*20, [1]*20, 'o', ms=12,c='gray', label='hold')
        ax.plot([0]*20, [0]*20, '^', ms=12,c='blue', label='buy' )
        ax.plot([0]*20, [0]*20, 'v', ms=12,c='red', label='sell')
        
        ax2.bar(x=[99, 100, 101], height=[-5, 5, 10])

        ax.set_xlim(0,1)
        ax.set_ylim(0,1)
        ax.legend()
        ax.set_xlabel('timesteps')
        ax.grid()
        ax.set_title('actions')
        
        self.ax = ax
        self.ax2 = ax2
        self.fig = fig

        self.bids =[]
        self.asks =[]
        self.x =[]

        self.minprice = 10000000
        self.maxprice = 0
        
#         fig.set_size_inches(5,5, forward = False)
        # 
#         self.fig.canvas.layout

    def updateLOB(self, LOBstate):
        self.ax2.cla()
        LOBstate.plot.bar(ax=self.ax2)

        # self.ax2.bar(x=LOBstate.index, height=LOBstate.values)

    def update(self, ts, bestbid, bestask, LOBstate):             
        # update lob
        self.updateLOB(LOBstate)

        # update price
        lineBids = self.ax.lines[0]
        lineAsks = self.ax.lines[1]

        self.bids.append(bestbid)
        self.asks.append(bestask)
        self.x.append(ts)

        # line.set_xdata(range(len(x)))
        lineBids.set_xdata(self.x)
        lineAsks.set_xdata(self.x)
        lineBids.set_ydata(self.bids)
        lineAsks.set_ydata(self.asks)
        
        # update action plots
        # for i, line in enumerate(self.ax.lines[1:]):
        #     line.set_xdata(np.argwhere(actions==i).T)
        #     line.set_ydata(x[actions==i])
        #     line.set_marker(['o','^','v'][i])

        # update limits
        self.ax.set_xlim(0, ts)

        if bestask<self.minprice:
            self.minprice = bestask
        if bestbid<self.minprice:
            self.minprice = bestbid
        if bestask>self.maxprice:
            self.maxprice = bestask
        if bestbid>self.maxprice:
            self.maxprice = bestbid
        
        self.ax.set_ylim(self.minprice, self.maxprice)
        self.fig.canvas.draw()