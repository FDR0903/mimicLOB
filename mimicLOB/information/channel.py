# -*- coding: utf-8 -*-
"""
Created on Thu Apr 12 19:01:34 2018

The Channel a class is a doubly linked chain of news.

@author: FDR
"""

""" 
Imports
"""
import time, random
from .news import news
        
class Channel(object):
    '''
    A doubly linked list of News. Used to iterate through news.
    '''

    def __init__(self):
        self.head_news = news(50) # first news  in the list
        self.tail_news = self.head_news # last news in the list
        self.length = 0 # number of News in the list
        self.last = None # helper for iterating
        self.name = 'AFP' # name of the channel

    def __len__(self):
        return self.length

    def __iter__(self):
        self.last = self.head_news
        return self
    
    def __str__(self):
        return self.name

    def next(self):
        '''Get the next news in the list.

        Set self.last as the next news. If there is no next order, stop
        iterating through list.
        '''
        if self.last == None:
            raise StopIteration
        else:
            return_value = self.last
            self.last = self.last.next_news
            return return_value

    def get_head_news(self):
        return self.head_news

    def get_tail_news(self):
        return self.tail_news

    def get_latest_news(self):
        return self.get_tail_news()


    def append_news(self, news):
        if len(self) == 0:
            news.next_news = None
            news.prev_news = None
            self.head_news = news
            self.tail_news = news
        else:
            news.prev_news = self.tail_news
            news.next_news = None
            self.tail_news.next_news = news
            self.tail_news = news
        
        self.length +=1


    __next__ = next # python3

    