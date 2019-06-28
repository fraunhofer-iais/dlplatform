from DLplatform.baseClass import baseClass

from abc import ABCMeta
from typing import List
from DLplatform.parameters import Parameters

class Aggregator(baseClass):
    '''
    Base class for aggregating mechanisms.
    Inherited from BaseClass with Technical Logger. Method __call__ should be implemented 
    for a particular class implementing specific method of models aggregation (e.g. Average)

    '''

    __metaclass__ = ABCMeta

    def __init__(self, name = "Aggregator"):
        '''
        Initialize BaseClass parent with name Aggregator

        Returns
        -------
        None
        '''
        baseClass.__init__(self, name = name)

    def __call__(self, params : List[Parameters]) -> Parameters:
        '''
        Aggregator call method, combines Parameters into one model's Parameters
        Specific implementation is different for different approaches.

        Parameters
        ----------
        params - list with Parameters of models to be aggregated

        Returns
        -------
        Parameters object for the aggregated model

        '''

        raise NotImplementedError
        