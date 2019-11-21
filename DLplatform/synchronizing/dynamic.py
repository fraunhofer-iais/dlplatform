
from DLplatform.synchronizing.synchronizer import Synchronizer
from DLplatform.parameters import Parameters

from typing import List
import numpy as np
import random

class DynamicSync(Synchronizer):
    '''
    Mechanism of dynamic synchronization
    Inherited from Synchronizer. Main method called by Coordinator is evaluate.
    This dynamic synchronization protocol performs a full synchronization as soon as 
    a violation occurs. This is the most basic form of resolution protocol.
    '''

    def __init__(self, delta: float, refPoint = None, name = "DynamicSync"):
        '''
        Initialize BaseClass parent with name DynamicSync

        Parameters
        ----------
        delta - sets the maximum divergence threshold

        Returns
        -------
        None
        '''
        Synchronizer.__init__(self, name = name)
        self._delta = delta
        self._refPoint = refPoint
    
    def evaluate(self, nodesDict, activeNodes: List[str], allNodes: List[str]) -> (List[str], Parameters):
        '''
        Mechanism of finding the averaged model
        Aggregator is called only in case when the nodes in balancing process 
        are all the registered nodes. When there is at least one violation the 
        returned list of nodes to take part in the balancing is the list of all the
        registered nodes. As long as aggregator was not called the returned params 
        are None. As long as there are None among param for the node that is still active 
        it means that not all 
        the requested nodes for balancing returned the parameters and aggregation 
        still cannot be called.

        Parameters
        ----------
        nodesDict - dictionary of nodes' identifiers as keys and their parameters as values that are in violation or requested for balancing
        activeNodes - list of nodes' identifiers that are active currently
        allNodes - list of nodes' identifiers that were taking part in learning

        Returns
        -------
        list of nodes' identifiers that are taking part in balancing
        parameters of the aggregated model

        Exceptions
        ----------
        AttributeError
            in case no aggregator was set for aggregating models' parameters into averaged
        '''
        if self._aggregator is None:
            self.error("No aggregator is set")
            raise AttributeError("No aggregator is set")

        if set(list(nodesDict.keys())) == set(allNodes):
            for id in nodesDict:
                if id in set(activeNodes) and nodesDict[id] is None:
                    # not all nodes for which parameters have been requested have answered. Thus, we wait.
                    return [], None, {}
                # this only can happen when we already have deactivated nodes, so hopefully by that time we have a reference point
                # so instead of deactivated node parameters, that we cannot request, we take reference point value
                elif not id in set(activeNodes):
                    nodesDict[id] = self._refPoint
            newModel = self._aggregator(list(nodesDict.values()))
            self._refPoint = newModel.getCopy()
            return activeNodes, newModel, {"setReference":True}
        else:
            # there is a violation and we are not waiting for requested models. Thus we trigger a full synchronization.
            return allNodes, None, {}

    def __str__(self):
        return "Dynamic synchronization, delta=" + str(self._delta)
        
class DynamicHedgeSync(DynamicSync):
    '''
    Mechanism of dynamic synchronization
    Inherited from Synchronizer. Main method called by Coordinator is evaluate.
    This dynamic sync protocol has the following resolution strategy:
        - If a violation occurs, one additional learner is queried for its model. 
            With this, a local balancing is attempted. 
        - If local balancing does not succeed, two additional learners are queried, 
            then 4, 8, and so on, until half of the set of learners have been queried. 
            If that still is unsuccessful, a full synchronization is triggered.
    '''

    def __init__(self, delta: float, refPoint = None, name = "DynamicHedgeSync"):
        '''
        Initialize BaseClass parent with name DynamicHedgeSync
        Sets delta and refPoint

        Parameters
        ----------
        delta - sets the maximum divergence threshold
        refPoint - sets the reference model against which the averaged parameters
            are checked - if violation still occurs

        Returns
        -------
        None
        '''
        Synchronizer.__init__(self, name = name)
        self._delta = delta
        self._refPoint = refPoint
        
    def evaluate(self, nodesDict, activeNodes: List[str], allNodes: List[str]) -> (List[str], Parameters):
        '''
        Mechanism of finding the averaged model
        Aggregator is called both in case when the nodes in balancing process 
        are all the registered nodes and when all the requested nodes returned 
        parameters, i.e., param does not include None. If it is not full synchronization 
        resulting model is checked for violation. While violation occurs the set of nodes 
        for balancing is augmented.

        Parameters
        ----------
        nodesDict - dictionary of nodes' identifiers as keys and their parameters as values that are in violation or requested for balancing
        activeNodes - list of nodes' identifiers that are active currently
        allNodes - list of nodes' identifiers that were taking part in learning

        Returns
        -------
        list of nodes' identifiers that are taking part in balancing
        parameters of the aggregated model

        Exceptions
        ----------
        AttributeError
            in case no aggregator was set for aggregating models' parameters into averaged
        '''
        if self._aggregator is None:
            self.error("No aggregator is set")
            raise AttributeError("No aggregator is set")

        for id in nodesDict:
            if id in set(activeNodes) and nodesDict[id] is None:
                # not all nodes for which parameters have been requested have answered. Thus, we wait.
                return [], None, {}
            # this only can happen when we already have deactivated nodes, so hopefully by that time we have a reference point
            # so instead of deactivated node parameters, that we cannot request, we take reference point value
            elif not id in set(activeNodes):
                nodesDict[id] = self._refPoint

        if set(list(nodesDict.keys())) == set(allNodes):
            #i.e., a full sync was triggered and we have received all models.
            newModel = self._aggregator(list(nodesDict.values()))
            self._refPoint = newModel.getCopy()
            return activeNodes, newModel, {"setReference":True}
        else:
            #first, try local balancing:
            newModel = self._aggregator(list(nodesDict.values()))
            if self._refPoint is None:
                dist = self._delta + 1.0 #if refpoint is None (at initialization), the distance is set to ensure a violation
            else:
                dist = newModel.distance(self._refPoint)
            if dist <= self._delta:
                # updating only active nodes
                updateNodes = list(set(list(nodesDict.keys())).intersection(set(activeNodes)))
                return updateNodes, newModel, {}
            else:
                # allow to request for balancing even inactive nodes
                requestSet = self.augmentBalancingSet(list(nodesDict.keys()), allNodes)
                if len(set(requestSet).union(set(list(nodesDict.keys())))) >= (len(allNodes) / 2):
                    #if the balancing set grew to more than half of all learners, trigger 
                    #a full sync instead of a local synchronization. This is a hedging 
                    #strategy to avoid endless local balancing.
                    return allNodes, None, {}
                return requestSet, None, {}
            
    def augmentBalancingSet(self, nodes: List[str], registeredNodes: List[str]) -> List[str]:
        '''
        Mechanism of augmenting the set of nodes in balancing procedure
        Randomly sample twice more nodes than are currently involved in balancing
        from the left among registered. In case there are not enough nodes 
        just all the left nodes are returned.

        Parameters
        ----------
        nodes - list of nodes' identifiers that are in violation or requested for balancing
        registredNodes - list of nodes' identifiers that are registered on Coordinator

        Returns
        -------
        list of nodes' identifiers that are proposed for balancing
        '''
        potentialNodes = set(registeredNodes).difference(set(nodes))
        requiredAmount = 2*len(nodes)
        if len(potentialNodes) <= requiredAmount:
            newNodes = potentialNodes
        else:
            newNodes = random.sample(potentialNodes, requiredAmount)
        return newNodes
    
    def __str__(self):
        return "Dynamic hedge synchronization, delta=" + str(self._delta)
