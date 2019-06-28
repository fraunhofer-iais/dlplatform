
from DLplatform.baseClass import baseClass
from DLplatform.parameters import Parameters
from DLplatform.aggregating import Aggregator

from abc import ABCMeta
from typing import List

class Synchronizer(baseClass):
    '''
    Abstract class defining main methods of any synchronization mechanism
    All the synchronisation mechanisms (e.g. static and dynamic) should be
    inherited from this class. This class knows about aggregator that is 
    used for creation of an averaged model.
    '''

    __metaclass__       = ABCMeta

    def __init__(self, name = "Synchronizer"):
        '''
        Initialize BaseClass parent with name Synchronizer
        Sets up aggregator to None

        Returns
        -------
        None
        '''
        baseClass.__init__(self, name = name)

        self._aggregator         = None

    def setAggregator(self, agg : Aggregator):
        '''
        Setter for an aggregator

        Parameters
        ----------
        agg : Aggregator

        Returns
        -------
        None

        Exception
        --------
        ValueError
            in case that agg is not a Aggregator
        '''

        if not isinstance(agg, Aggregator):
            error_text = "The attribute agg is of type " + str(type(agg)) + " and not of type" + str(Aggregator)
            self.error(error_text)
            raise ValueError(error_text)

        self._aggregator = agg

    def getAggregator(self) -> Aggregator:
        '''
        Getter of an aggregator

        Returns
        -------
        Aggregator currently set up in the synchronizer

        '''

        return self._aggregator

    def evaluate(self, nodes: List[str], param: List[Parameters], registeredNodes: List[str]) -> (List[int], Parameters):
        '''
        Main method that should be implemented by a particular
        synchronization mechanism. This is the method called 
        by Coordinator during balancing process.

        Parameters
        ----------
        nodes - list of nodes' identifiers that are in violation or requested for balancing
        param - parameters of the nodes in violation or requested for balancing
        registredNodes - list of nodes' identifiers that are registered on Coordinator

        Returns
        -------
        list of nodes' identafiers that are needed for balancing in case when aggregation
            was not yet performed or list of nodes that should receive an averaged model
            if aggregation was performed
        parameters of the averaged model, in case it is None Coordinator will request the 
            returned list of nodes for their parameters in order to try to perform 
            balancing once again
        '''

        raise NotImplementedError