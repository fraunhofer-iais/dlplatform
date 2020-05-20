from DLplatform.baseClass import baseClass
from DLplatform.parameters import Parameters

from typing import List
from multiprocessing import Process
from abc import ABCMeta

class Communicator(baseClass, Process):
    '''
    Abstract class for incapsulating all the methods for sending
    and receiving messages in the distributed system
    '''

    __metaclass__ = ABCMeta

    def __init__(self, name = "Communicator"):
        '''
        Initializes the BaseClass with name Communicator

        Parameters
        ----------
        name : str
            identifier for logging
        '''

        Process.__init__(self)
        baseClass.__init__(self, name = name)

        self._consumerConnection    = None
        self.learningLogger         = None

    def setLearningLogger(self, learningLogger):
        '''
        Logger in order to keep track of all the messages sent through communicator
        This is later used for measured communication effectiveness of the learning process
        '''
        self.learningLogger = learningLogger

    # the point where it is still to RabbitMQ oriented, should be much more high level
    def _onMessageReceived(self, ch, method, properties, body):
        '''
        Pushes the consumed message from external communication into the interprocess
        communication queue

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
        self._consumerConnection.put(msg)

    def setConnection(self, consumerConnection):
        '''
        Setter for the interprocess connection queue

        Parameters
        ----------
        consumerConnection : Connection
            the connection queue between the communicator and the consumer (that can be worker or coordinator)
        '''

        self._consumerConnection = consumerConnection
        self.info("Consumer connection was set")

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

        if (self._consumerConnection == None):
            raise AttributeError("Consumer connection wasn't set properly!")

        super().start()

    def run(self):
        '''
        Method that is run as target of the thread with communicator
        '''

        pass