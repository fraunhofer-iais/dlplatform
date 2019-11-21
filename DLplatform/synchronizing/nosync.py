
from DLplatform.synchronizing.synchronizer import Synchronizer
from DLplatform.parameters import Parameters
from typing import List

class NoSync(Synchronizer):
    def __init__(self, name = "NoSync"):
        Synchronizer.__init__(self, name = name)
    
    def evaluate(self, nodesDict, activeNodes: List[str], allNodes: List[str]) -> (List[str], Parameters):
        if len(nodes) > 1:
            self.error("More than one node sent its model for nosync.")
            raise AttributeError("More than one node sent its model for nosync.")
        return [list(nodesDict.keys())[0]], list(nodesDict.values())[0], {"nosync": True}

    def __str__(self):
        return "No sync"
        
        
