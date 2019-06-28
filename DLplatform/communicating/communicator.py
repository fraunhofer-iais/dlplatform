from DLplatform.baseClass import baseClass
from DLplatform.parameters import Parameters

from typing import List
from multiprocessing import Process
from abc import ABCMeta
#from multiprocessing import Connection
from pickle import dumps, loads

INITIAL_MODEL_REQUEST           = "INITIAL_MODEL"
VIOLATION_OBTAINED              = "VIOLATION"
ANSWER_TO_COORDINATOR_REQUEST   = "MODEL_REQUEST"
SEND_BALANCING_REQUEST          = "BALANCING_REQUEST"
SEND_AVERAGED_MODEL             = "AVERAGED_MODEL"

class NoneConnection:
    '''
    Used to flag that no learner Pipe is available
    '''
    pass

class Communicator(baseClass, Process):
    '''
    Abstract class for incapsulating all the methods for sending
    and receiveing messages in the distributed system
    '''

    __metaclass__ = ABCMeta

    def __init__(self,
                 name           = "Communicator"):
        '''

        Initializes the BaseClass with name Communicator

        Parameters
        ----------
        name : str
            identifier for logging
        '''

        Process.__init__(self)
        baseClass.__init__(self, name = name)
        self._workerConnection  = None
        self.learningLogger    = None

    def setLearningLogger(self, learningLogger):
        self.learningLogger = learningLogger

    def _onMessageReceived(self, ch, method, properties, body):
        '''

        Parameters
        ----------
        default parameters from RabbitMQ for callback; body contains the message itself

        Returns
        -------
        None

        '''

        self.info("received message " + method.routing_key)

        routing_key = method.routing_key
        exchange = method.exchange

        msg = (routing_key, exchange, body)
        #msg = dumps(msg)

        self._workerConnection.send(msg)

    def setConnections(self,
                       workerConnection):
        '''

        Setter for the connections to worker and from learner

        Parameters
        ----------
        workerConnection : Connection
            the transmitter connection of a simplex pipe between the communicator and the worker
        '''

        #if isinstance(workerConnection,Connection):
        self._workerConnection    = workerConnection
        #else:
        #    raise ValueError("Attribute workerConnection is not of type Connection, it is of type" + str(type(workerPipe)))
        self.info("workerconnection was set!")

    def initiate(self):
        '''
        Initializes the consuming messages thread
        '''
        pass

    def sendViolation(self, identifier : str, param : Parameters):
        '''
        Publish message about violation
        '''

        raise NotImplementedError

    def sendRegistration(self, identifier : str, param : Parameters):
        '''
        Publish message that will register a new node on coordinator
        '''

        raise NotImplementedError

    def sendDeregistration(self, identifier : str):
        raise NotImplementedError

    def sendParameters(self, identifier : str, param : Parameters):
        '''
        Publish message with parametres
        '''

        raise NotImplementedError

    def sendBalancingRequest(self, identifier : str):
        '''
        Publish message to query the worker for its current parameters
        '''

        raise NotImplementedError

    def sendAveragedModel(self, identifiers : List[str], param : Parameters, flags: dict):
        '''
        Publish message to send an averaged model to the nodes
        '''

        raise NotImplementedError

    def start(self):
        '''
        implementation of the start function of process parent class
        '''

        super().start()

        if (self._workerConnection == None):
            raise AttributeError("workerConnection wasn't set properly!")

    def run(self):
        '''
        Method that is run as target of the thread with communicator
        '''

        pass

