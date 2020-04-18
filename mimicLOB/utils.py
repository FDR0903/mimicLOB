import pandas as pd

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