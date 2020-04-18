# -*- coding: utf-8 -*-
"""
Created on Thu Apr 12 19:01:34 2018

The information object is an object that will send, given an intensity, good or bad information to agents.

Goodness of information is given on a scale from 0 to 100.

Depending on the type of agent, she will react to information. Basic reaction is shifting up 
the probability of buying if a good information comes, and shifting down probability of selling, accoring to how
strong the information is good. and vice versa.

@author: FDR
"""

""" 
Imports
"""
from abc import ABC, abstractmethod, ABCMeta
from sortedcontainers import SortedDict
from .channel import news
import numpy as  np
import datetime

from random import randint, randrange

class genericInformation(ABC):
    def __init__(self, **kwargs):
        self.__dict_params = kwargs
        intensity = self.dict_params['intensity']
        self.PoissonPath = np.random.poisson(intensity, 1000)
        self.Pathposition = 0
        self.channel   = self.dict_params['channel']
        self.Job = None
        self.verbose = self.dict_params['verbose'] if 'verbose' in self.dict_params else False
    @property
    def dict_params(self):
        return self.__dict_params

    def notify(self):
        if self.Pathposition == 1000: self.Pathposition = 0
        if self.PoissonPath[self.Pathposition] == 1:
            # generate a news
            info = randrange(0, 100, 1)
            if self.verbose:
                print('#################################################################')
                print(f'NEWS : {info}')
                print('#################################################################')
            self.channel.append_news(news(info))
        self.Pathposition += 1

    def start(self, sched):
        self.Job = sched.add_job(self.notify, 'interval', seconds=0.001, jitter=0.1)
        
    def stop(self, sched):
        if self.Job:  self.Job.remove()       
        self.Job = None

    # def act(self):
    #     self.Job = self.scheduler.add_job(self.notify, 'interval', seconds=1, jitter=0.5)

    # def stop(self):
    #     if self.Job is not None:  self.Job.remove()       
    #     self.Job = None    

        
    """
    GETTERS
    """
