from DLplatform.synchronizing.synchronizer import Synchronizer
from DLplatform.parameters import Parameters
from typing import List

class PeriodicSync(Synchronizer):
    '''

    PeriodicSync inherits from abstract class Synchronizer and implements method "evaluate" for the case of periodic model averaging.

    '''
    def __init__(self, name = "PeriodicSync"):
        Synchronizer.__init__(self, name = name)
    
    def evaluate(self, nodesDict, activeNodes: List[str], allNodes: List[str]) -> (List[str], Parameters):
        '''

        Periodic synchronization mechanism. This method is called by the coordinator during the balancing process.

        Parameters
        ----------
        nodesDict - dictionary of node identifiers as keys and their parameters as values that are in violation or requested for balancing
        activeNodes - list of nodes' identifiers that are active currently
        allNodes - list of nodes' identifiers that were taking part in the learning

        Returns
        -------
        list of node identifiers that receive the averaged model after aggregation is performed
        parameters of the averaged model

        '''

        if self._aggregator is None:
            self.error("No aggregator is set")
            raise AttributeError("No aggregator is set")

        # this condition is needed to call the 'evaluate' method in a standardized way across the different sync schemes
        if set(list(nodesDict.keys())) == set(activeNodes):
            return activeNodes, self._aggregator(list(nodesDict.values())), {}
        else:
            return [], None, {}

    def __str__(self):
        return "Periodic synchronization"
