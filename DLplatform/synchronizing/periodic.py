from DLplatform.synchronizing.synchronizer import Synchronizer
from DLplatform.parameters import Parameters
from typing import List

class PeriodicSync(Synchronizer):
    '''

    PeriodicSync inherits from abstract class Synchronizer and implements method "evaluate" for the case of periodic model averaging.

    '''
    def __init__(self, name = "PeriodicSync"):
        Synchronizer.__init__(self, name = name)
    
    def evaluate(self, nodes: List[str], param: List[Parameters], registeredNodes: List[str]) -> (List[str], Parameters):
        '''

        Periodic synchronization mechanism. This method is called by the coordinator during the balancing process.

        Parameters
        ----------
        nodes - list of node identifiers that are in violation or requested for balancing
        param - parameters of the nodes in violation or requested for balancing
        registeredNodes - list of nodes' identifiers that are registered at the coordinator

        Returns
        -------
        list of node identifiers that receive the averaged model after aggregation is performed
        parameters of the averaged model

        '''

        if self._aggregator is None:
            self.error("No aggregator is set")
            raise AttributeError("No aggregator is set")

        # this condition is needed to call the 'evaluate' method in a standardized way across the different sync schemes
        if set(nodes) == set(registeredNodes):
            return registeredNodes, self._aggregator(param), {}
        else:
            return [], None, {}

    def __str__(self):
        return "Periodic synchronization"
