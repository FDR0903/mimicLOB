
# -*- coding: utf-8 -*-
"""
Created on Thu Apr 12 19:01:34 2018

The News Class is an object with a time stamp, a news value between 0 and 100, and a link to previous and next news.

@author: Fayçal Drissi
"""

""" 
Imports
"""

class news(object):
    '''
    News are doubly linked and have helper functions (next, prev)
    '''
    def __init__(self, val):
        # doubly linked list to make it easier to re-order Orders for a particular price point
        self.next_news = None
        self.prev_news = None
        self.val = val

    # helper functions to get Orders in linked list
    def next_news(self):
        return self.next_news

    def prev_news(self):
        return self.prev_news
        