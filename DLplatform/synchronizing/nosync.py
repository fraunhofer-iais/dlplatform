
from DLplatform.synchronizing.synchronizer import Synchronizer
from DLplatform.parameters import Parameters
from typing import List

class NoSync(Synchronizer):
    def __init__(self, name = "NoSync"):
        Synchronizer.__init__(self, name = name)
    
    def evaluate(self, nodes: List[str], param: List[Parameters], registeredNodes: List[str]) -> (List[str], Parameters):
        if len(nodes) > 1:
            self.error("More than one node sent its model for nosync.")
            raise AttributeError("More than one node sent its model for nosync.")
        return [nodes[0]], param[0], {"nosync": True}

    def __str__(self):
        return "No sync"
        
        
