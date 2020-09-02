from DLplatform.baseClass import baseClass
from DLplatform.parameters import Parameters
from DLplatform.communicating import Communicator
from DLplatform.synchronizing import Synchronizer

from pickle import loads
from multiprocessing import Queue
import sys

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
    def __call__(self, params : Parameters):
        return params
    
class UseFirstInitHandler(InitializationHandler):
    def __init__(self):
        self._initParams = None
    
    
    def __call__(self, params : Parameters):
        if self._initParams is None:
            self._initParams = params
        return self._initParams
    
## %TODO finish implementation of noisy initialization
class NoisyInitHandler(InitializationHandler):
    def __init__(self, noiseParams):
        self._noiseParams = noiseParams
        self._initParams = None
    
    def __call__(self, params : Parameters):
        if self._initParams is None:
            self._initParams = params
        eps = self.getNoise()
        return self._initParams.add(eps)
    
    def getNoise(self):
        if self._noiseParams['type'] == "uniform":
            range = self._noiseParams['range']
        return None

class Coordinator(baseClass):

    '''
    Provides the functionality of the central coordinator which handles model
    synchronization and information exchange between workers
    '''    
    
    def __init__(self, nodesToWait = None, minActive = 0):
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
        
        self._communicator              = None
        self._synchronizer              = None
        self._violations                = []
        self._nodesInViolation          = []
        self._balancingSet              = {}
        self._activeNodes	            = []
        self._initHandler               = InitializationHandler()
        self._learningLogger            = None
        # if this parameter is set, then the coordinator will wait till all the nodes are registered
        self._nodesToWait               = nodesAmount
        self._waitingNodes              = {}
        # if this parameter is larger than 0, then when less than this amount of workers is active,
        # process stops - all the other still active workers are asked to exit
        self._minActive                 = minActive

        # initializing queue for communication with communicator process
        self._communicatorConnection    = Queue()

    def setLearningLogger(self, logger):
        self._learningLogger = logger

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

    def getSynchronizer(self) -> Synchronizer:
        '''

        Returns
        -------
        Synchronizer

        '''

        return self._synchronizer

    def checkInterProcessCommunication(self):
        '''
        Checks queue for new incoming messages and acts in case if a message has arrived

        Exceptions
        ----------
        ValueError
            in case that the received message doesn't fit with the expected type
        '''

        if not self._communicatorConnection.empty():
            recvObj = self._communicatorConnection.get()

            if not isinstance(recvObj,tuple):
                raise ValueError("coordinator received recvObj that is not a tuple")
            elif not len(recvObj) == 3:
                raise ValueError("coordinator received recvObj which has length different from 3")

            routing_key, exchange, body = recvObj
            self.onMessageReceived(routing_key, exchange, body)

    def _setConnectionsToComponents(self):
        '''

        Gives communicator access to the queue such that an inter process communication can take place.

        Exceptions
        ----------
        AttributeError
            in case if no communicator is set

        '''

        if self._communicator is None:
            self.error("Communicator not set!")
            raise AttributeError("Communicator not set!")

        self._communicator.setConnection(consumerConnection = self._communicatorConnection)

    def onMessageReceived(self, routing_key, exchange, body):
        message = loads(body)
        message_size = sys.getsizeof(body)
        if routing_key == 'violation':
            self.info("Coordinator received a violation")
            self._communicator.learningLogger.logViolationMessage(exchange, routing_key, message['id'], message_size, 'receive')
            self._violations.append(body)
        if routing_key == 'balancing':
            self.info("Coordinator received a balancing model")
            self._communicator.learningLogger.logBalancingMessage(exchange, routing_key, message['id'], message_size, 'receive')
            # append it to violations - thus we enter the balancing process again
            # model can send the answer to balancing request only once - then it will be waiting 
            # for a new model to come and will not react to requests anymore
            # so it cannot be that the model answers several times and thus initiates new 
            # balancing when not needed
            self._violations.append(body)
        if routing_key == 'registration':
            self.info("Coordinator received a registration")
            self._communicator.learningLogger.logRegistrationMessage(exchange, routing_key, message['id'], message_size, 'receive')
            
            nodeId = message['id']
            self._learningLogger.logModel(filename = "initialization_node" + str(message['id']), params = message['param'])
            newParams = self._initHandler(message['param'])
            self._learningLogger.logModel(filename = "startState_node" + str(message['id']), params = message['param'])
            self._activeNodes.append(nodeId)
            if self._nodesToWait is None:
                self._communicator.sendAveragedModel(identifiers = [nodeId], param = newParams, flags = {"setReference":True})
            else:
                self._waitingNodes[nodeId] = newParams
                # we send around the initial parameters only when all the expected nodes are there
                if len(self._waitingNodes) == self._nodesToWait:
                    for id in self._waitingNodes:
                        self._communicator.sendAveragedModel(identifiers = [id], param = self._waitingNodes[id], flags = {"setReference":True})
                    self._waitingNodes.clear()
                    self._nodesToWait = None
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
            if not self._balancingSet.get(message['id']) is None:
                self._balancingSet.pop(message['id'])
            if not self._minActive == 0 and len(self._activeNodes) < self._minActive:
                self.info("Not enough active workers left, exiting.")
                for nodeId in self._activeNodes:
                    self._communicator.sendExitRequest(nodeId)
                # we do not want to send exit messages again
                self._minActive = 0
            if len(self._activeNodes) == 0:
                self.info("Training finished, exiting.")
                sys.exit()

    def run(self):
        if self._communicator is None:
            self.error("Communicator is not set!")
            raise AttributeError("Communicator is not set!")

        if self._synchronizer is None:
            self.error("Synchronizing operator is not set!")
            raise AttributeError("Synchronizing operator is not set!")

        self._communicator.initiate(exchange = self._communicator._exchangeCoordinator,
                                    topics = ['registration', 'deregistration', 'violation', 'balancing'])
        self._communicator.daemon = True

        self._setConnectionsToComponents()

        self._communicator.start()

        if (self._communicatorConnection == None):
            raise AttributeError("communicatorConnection was not set properly at the worker!")

        while True:
            self.checkInterProcessCommunication()
            # we have to enter this in two cases:
            # - we got a violation
            # - we did not get all the balancing models
            if len(self._violations) > 0 or len(self._balancingSet.keys()) != 0:
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
                nodes, params, flags = self._synchronizer.evaluate(self._balancingSet, self._activeNodes)
                # fill balancing set with None for new nodes in balancing set
                for newNode in nodes:
                    if not newNode in self._balancingSet.keys():
                        self._balancingSet[newNode] = None

                if params is None and None in self._balancingSet.values():
                    # request for models from balancing set nodes
                    for newNode in nodes:
                        # balancingRequest can be sent only when it is dynamic averaging
                        if self._balancingSet[newNode] is None and newNode in self._activeNodes:
                            self._communicator.sendBalancingRequest(newNode)
                elif not params is None:
                    # we do not want to update the nodes that are already inactive
                    nodesToSendAvg = list(set(nodes) & set(self._activeNodes))
                    self._communicator.sendAveragedModel(nodesToSendAvg, params, flags)
                    self._learningLogger.logBalancing(flags, self._nodesInViolation, list(self._balancingSet.keys()))
                    self._learningLogger.logAveragedModel(nodes, params, flags)
                    self._balancingSet.clear()
                    self._nodesInViolation = []

        self._communicator.join()
