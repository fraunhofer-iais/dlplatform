from DLplatform.synchronizing.synchronizer import Synchronizer
from DLplatform.parameters import Parameters
from typing import List


class AggregationAtTheEnd(Synchronizer):
    def __init__(self, name = "Aggregation-at-the-end"):
        Synchronizer.__init__(self, name = name)
    
    def evaluate(self, nodesDict, activeNodes: List[str], allNodes: List[str]) -> (List[str], Parameters):

        if self._aggregator is None:
            self.error("No aggregator is set")
            raise AttributeError("No aggregator is set")

        # this condition is needed to call the 'evaluate' method in a standardized way across the different sync schemes
        if set(list(nodesDict.keys())) == set(activeNodes):
            return activeNodes, self._aggregator(param), {}
        else:
            return [], None, {}

    def __str__(self):
        return "Aggregation-at-the-end synchronization"
