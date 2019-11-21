from DLplatform.baseClass import baseClass
from DLplatform.parameters import Parameters
from DLplatform.communicating import Communicator
from DLplatform.communicating.communicator import SEND_AVERAGED_MODEL, SEND_BALANCING_REQUEST
from DLplatform.synchronizing import Synchronizer

from pickle import loads, dumps
from multiprocessing import Pipe
from typing import List, Dict
import time
import sys
import numpy.random as rd

'''
    The InitializationHandler defines, how the coordinator handles model parameters when new learners register. 
    In the base case (InitializationHandler), it will leave the models untouched (standard setting). Each learner
    is initialized individually in the way it was defined in the learner factory.
    
    UseFirstInitHandler uses the first model it receives (i.e., the from the first learner that registers at the coordinator)
    as initial parameters for all other learners. This ensures that all learners start with the exact same parameters.
    
    NoisyInitHandler does the same as UseFirstInitHandler, but adds noise to the parameters. Thus, all learners are initialized
    around the same common parameters.
'''
class InitializationHandler:
    def __init__(self):
        self._initRefPoint = None
    
    '''
        returns the initialization parameters and the initial reference point
    '''
    def __call__(self, params : Parameters):
        if self._initRefPoint is None:
            self._initRefPoint = params
        return params, self._initRefPoint
    
class UseFirstInitHandler(InitializationHandler):
    def __init__(self):
        self._initParams = None
        self._initRefPoint = None
    
    
    def __call__(self, params : Parameters):
        if self._initParams is None:
            self._initParams = params
        if self._initRefPoint is None:
            self._initRefPoint = params
        return self._initParams, self._initRefPoint
    
class NoisyInitHandler(InitializationHandler):
    def __init__(self, noiseParams):
        self._noiseParams = noiseParams
        self._initParams = None
        self._initRefPoint = None
    
    def __call__(self, params : Parameters):
        if self._initParams is None:
            self._initParams = params
        if self._initRefPoint is None:
            self._initRefPoint = params
        eps = self.getNoise()
        return self._initParams.add(eps), self._initRefPoint
    
    def getNoise(self):
        if self._noiseParams['type'] == "uniform":
            range = self._noiseParams['range']
        return None

class Coordinator(baseClass):

    '''
    Provides the functionalities of the central coordinator which handles model synchronization and information exchange between workers
    '''    
    
    def __init__(self):
        '''

        Initializes a 'Coordinator' object.

        Parameters
        ----------

        Exception
        --------
        ValueError
            in case that identifier is not a string
        '''

        super().__init__(name = "Coordinator")
        
        self._communicator      = None
        self._synchronizer      = None
        self._violations        = []
        self._nodesInViolation  = []
        self._balancingSet      = {}
        self._activeNodes	= []
        self._initHandler       = InitializationHandler()
        self._learningLogger    = None
        self._allNodes		= []

        # initiallizing pipes for communication, in contrast to the worker, Coordinator can also send messages to
        # the communicator
        self._communicatorConnections = Pipe(duplex=True)

        # for retrival at the worker
        self._communicatorConnection = self._communicatorConnections[0]

    def setLearningLogger(self, logger):
        self._learningLogger = logger

    def onModelUpdate(self, param : Parameters, workerId : str):
        '''

        Parameters
        ----------
        param
        workerId

        Returns
        -------

        Exception
        --------
        ValueError
            in case that param and workerId are not of type Parameters or/and str, respectively.
        '''

        raise NotImplementedError

    def setCommunicator(self, comm : Communicator):
        '''

        Links a 'Communicator' object to the 'Coordinator' object.

        Parameters
        ----------
        comm: object - 'Communicator' object that handles message passing for the coordinator

        Returns
        -------

        Exception
        --------
        ValueError
            in case that identifier is not a Communicator
        '''

        if not isinstance(comm,Communicator):
            error_text = "The attribute comm is of type " + str(type(comm)) + " and not of type" + str(Communicator)
            self.error(error_text)
            raise ValueError(error_text)

        self._communicator = comm

    def getCommunicator(self) -> Communicator:
        '''

        Get 'Communicator' object of the coordinator.

        Returns
        -------
        _communicator: object - 'Communicator' object that handles message passing for the coordinator

        '''

        return self._communicator

    def setInitHandler(self, initHandler : InitializationHandler):
        self._initHandler = initHandler

    #def getInitialParams(self):
    #    return self._initialParam

    def setSynchronizer(self, synOp : Synchronizer):
        '''

        Parameters
        ----------
        synOp : Synchronizer

        Returns
        -------

        Exception
        --------
        ValueError
            in case that  synOp is not a Synchronizer
        '''

        if not isinstance(synOp, Synchronizer):
            error_text = "The attribute synOp is of type " + str(type(synOp)) + " and not of type" + str(Synchronizer)
            self.error(error_text)
            raise ValueError(error_text)

        self._synchronizer = synOp

    def getSynchronizer(self) -> Synchronizer :
        '''

        Returns
        -------
        Synchronizer

        '''

        return self._synchronizer

    def retrieveMessages(self):
        '''
        checks pipes for new in coming messages and acts in case that a messages arrived. Since messages arriving from
        communicator are just those arriving at the communicator, we receive one type of message here.

        Exceptions
        ----------
        ValueError
            in case that the received message doesn't fit with the expected type
        '''
        if self._communicatorConnection.poll():

            recvObj     = self._communicatorConnection.recv()
            #recvObj = loads(recvObj)

            if not isinstance(recvObj,tuple):
                raise ValueError("worder received recvObj is not a tuple")
            elif not len(recvObj) == 3:
                raise ValueError("worder received recvObj, which has length of  different from 3")

            routing_key, exchange, body = recvObj
            self.onMessageReceived(routing_key, exchange, body)

    def _setConnectionsToComponents(self):
        '''

        distributes the transmitters and receiver connections over the different processes such that an inter process
        communication can take place.

        Exceptions
        ----------
        AttributeError
            in case if no communicator is set

        '''

        if self._communicator is None:
            self.error("Communicator not set!")
            raise AttributeError("Communicator not set!")

        # ToDo : bad style to set the leaner connection to the same as workerconnection, but it works! it should be
        # replaced
        self._communicator.setConnections   (workerConnection       = self._communicatorConnections[1])

    def onMessageReceived(self, routing_key, exchange, body):
        #self.info('STARTTIME_coordinator_onMessageReceived: '+str(time.time()))
        message     = loads(body)
        message_size = sys.getsizeof(body)
        if routing_key == 'violation':
            self.info("Coordinator received a violation")
            self._communicator.learningLogger.logViolationMessage(exchange, routing_key, message['id'], message_size, 'receive')
            self._violations.append(body)
        if routing_key == 'balancing':
            self.info("Coordinator received a balancing model")
            self._communicator.learningLogger.logBalancingMessage(exchange, routing_key, message['id'], message_size, 'receive')
            # append it to violations - thus we enter the balancing process again
            #@TODO: maybe some model received two requests and balancing is already done
            self._violations.append(body)
        if routing_key == 'registration':
            self.info("Coordinator received a registration")
            self._communicator.learningLogger.logRegistrationMessage(exchange, routing_key, message['id'], message_size, 'receive')
            
            nodeId = message['id']
            self._learningLogger.logModel(filename = "initialization_node" + str(message['id']), params = message['param'])
            newParams, newRefPoint = self._initHandler(message['param'])
            self._learningLogger.logModel(filename = "startState_node" + str(message['id']), params = message['param'])
            self._synchronizer._refPoint = newRefPoint
            self._communicator.sendAveragedModel(identifiers = [nodeId], param = newParams, flags = {"setReference":True})
            self._activeNodes.append(nodeId)
            self._allNodes.append(nodeId)
            #TODO: maybe we have to check the balancing set here again. 
            #If a node registered, while we are doing a full sync, or a balancing operation, 
            #we might need to check. But then, maybe it's all ok like this.
            #will spoil full sync for dynamic case and will spoil periodic case - they will have to wait
            # for this new node to make needed amount of updates
            # can check if balancing_set is not empty then just add this node to balancing set right away
            # and set its ability to train to false
        if routing_key == 'deregistration':
            self.info("Coordinator received a deregistration")
            self._communicator.learningLogger.logDeregistrationMessage(exchange, routing_key, message['id'], message_size, 'receive')
            self._learningLogger.logModel(filename = "finalState_node" + str(message['id']), params = message['param'])
            self._activeNodes.remove(message['id'])
            if len(self._activeNodes) == 0:
                self.info("No active workers left, exiting.")
                sys.exit()
        #self.info('ENDTIME_coordinator_onMessageReceived: '+str(time.time()))

    def run(self):
        if self._communicator is None:
            self.error("Communicator is not set!")
            raise AttributeError("Communicator is not set!")

        if self._synchronizer is None:
            self.error("Synchronizing operator is not set!")
            raise AttributeError("Synchronizing operator is not set!")

        self._communicator.initiate(exchange = self._communicator._exchangeCoordinator, topics = ['registration', 'deregistration', 'violation', 'balancing'])
        self._communicator.daemon = True

        self._setConnectionsToComponents()

        self._communicator.start()

        if (self._communicatorConnection == None):
            raise AttributeError("communicatorConnection was not set properly at the worker!")

        while True:
            self.retrieveMessages()
            # we have to enter this in two cases:
            # - we got a violation
            # - we did not get all the balancing models
            if len(self._violations) > 0 or len(self._balancingSet.keys()) != 0:
                #self.info('STARTTIME_coordinator_run: '+str(time.time()))
                if len(self._violations) > 0:
                    message = loads(self._violations[0])
                    nodeId = message['id']
                    param = message['param']
                    self._nodesInViolation.append(nodeId)
                    self._balancingSet[nodeId] = param
                    # @NOTE always deleting the current violation leads to potential extension of a dynamic small balancing to 
                    # a full_sync - might be a case that blocking everything, balancing one violation and then considering the next one
                    # is a better idea from the point of view of effectiveness
                    del self._violations[0]
                nodes, params, flags = self._synchronizer.evaluate(self._balancingSet, self._activeNodes, self._allNodes)
                # fill balancing set with None for new nodes in balancing set
                for newNode in nodes:
                    if not newNode in self._balancingSet.keys():
                        self._balancingSet[newNode] = None

                if params is None and None in self._balancingSet.values():
                    # request for models from balancing set nodes
                    for newNode in nodes:
                        if self._balancingSet[newNode] is None and newNode in self._activeNodes:
                            self._communicator.sendBalancingRequest(newNode)
                # None can still be there in _balancingSet,values() if the nodes are inactive and used for balancing
                # then reference point (previous average) is used instead
                elif not params is None:
                    self._communicator.sendAveragedModel(nodes, params, flags)
                    self._learningLogger.logBalancing(flags, self._nodesInViolation, list(self._balancingSet.keys()))
                    if set(nodes) == set(self._allNodes) or "nosync" in flags:
                        self._learningLogger.logAveragedModel(nodes, params, flags)
                    self._balancingSet.clear()
                    self._nodesInViolation = []
                #self.info('ENDTIME_coordinator_run: '+str(time.time()))

        self._communicator.join()
