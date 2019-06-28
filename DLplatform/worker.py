
from DLplatform.baseClass import baseClass
from DLplatform.learning.learner import Learner
from DLplatform.communicating import Communicator
from DLplatform.dataprovisioning import DataScheduler

import time
import pickle
from multiprocessing import Pipe
from pickle import loads, dumps
import sys

class Worker(baseClass):
    '''

    '''

    def __init__(self, identifier : str):
        '''

        Initialize a worker.

        Parameters
        ----------
        identifier : str

        Exception
        --------
        ValueError
            in case that identifier is not a string
        '''

        super().__init__(name = "worker_" + str(identifier))

        self._learner       = None
        self._communicator  = None
        self._dataScheduler = None
        self._identifier    = ""
        self._dataBuffer    = []

        self.setIdentifier(identifier = identifier)

        # initiallizing pipes for communication
        self._communicatorConnections   = Pipe(duplex=False)
        self._dataSourceConnections     = Pipe(duplex=False)

        # for retrival at the worker
        self._communicatorConnection    = self._communicatorConnections[0]
        self._dataSourceConnection      = self._dataSourceConnections[0]

    def setIdentifier(self, identifier : str):
        '''

        Set identifier of the worker.

        Parameters
        ----------
        identifier : str

        Exception
        --------
        ValueError
            in case that identifier is not a string
        '''

        if not isinstance(identifier, str):
            error_text = "The attribute identifier is of type " + str(type(identifier)) + " and not of type" + str(str)
            self.error(error_text)
            raise ValueError(error_text)

        self._identifier = identifier

    def getIdentifier(self) -> str:
        '''

        Get identifier of the worker.

        Returns
        -------
        str
        '''

        return  self._identifier

    def setLearner(self, learner : Learner):
        '''

        Set learner of the worker and link communicator and worker identifier with it

        Parameters
        ----------
        learner

        Returns
        -------

        Exception
        --------
        ValueError
            in case that learner is not of type Learner
        '''
        # @Todo: move this to worker run
        if self._communicator is None:
            self.error("Communicator not set!")
            raise AttributeError("Communicator not set!")

        if not isinstance(learner, Learner):
            self.error("the attribute learner is of type " + type(learner) + " and not of type" + Learner)
            raise ValueError("the attribute learner is of type " + type(learner) + " and not of type" + Learner)

        self._learner = learner
        self._learner.setIdentifier(self.getIdentifier())


    def getLearner(self) -> Learner:
        '''

        Get the learner of the worker.

        Returns
        -------
        Learner

        '''

        return self._learner

    def setCommunicator(self, comm : Communicator):
        '''

        Set the communicator of the worker.

        Parameters
        ----------
        comm

        Returns
        -------

        Exception
        --------
        ValueError
            in case that comm is not of type Communicator
        '''

        if not isinstance(comm, Communicator):
            error_text = "The attribute comm is of type " + str(type(comm)) + " and not of type" + str(Communicator)
            self.error(error_text)
            raise ValueError(error_text)

        self._communicator = comm

    def getCommunicator(self) -> Communicator:
        '''

        Get the communicator of the worker.

        Returns
        -------
        Communicator

        '''

        return self._commuicator

    def setDataScheduler(self, datascheduler : DataScheduler):
        '''

        Sets data scheduler of the worker and writes this info to the log file.

        Parameters
        ----------
        datascheduler

        Exception
        -------
        ValueError
            in case that datascheduler is not of type DataScheduler
        '''

        if not isinstance(datascheduler,DataScheduler):
            error_text = "The attribute datascheduler is of type " + str(type(datascheduler)) + " and not of type" + str(DataScheduler)
            self.error(error_text)
            raise ValueError(error_text)

        self._dataScheduler = datascheduler
        self.info("Set DataScheduler to " + self._dataScheduler.getName())

    def getDataScheduler(self) -> DataScheduler:
        '''

        Get data scheduler of the worker.

        Returns
        -------
        DataScheduler

        '''

        return self._dataScheduler

    def onDataUpdate(self, data: tuple):
        '''

        Defines how to process the next data point from the training dataset: Append it to the data buffer of the worker

        Parameters
        ----------
        data

        Returns
        -------

        '''
        self._dataBuffer.append(data)

    # the message might be either 
    # - initial model as answer to registration
    # - averaged model as answer to violation or balancing process
    # - averaged model together with reference model if there was a full update while balancing
    # - request to send parameters
    def onMessageReceived(self,  routing_key, exchange, body):
        '''

        Processes incoming message from coordinator:

        In case a new model arrives, this info is logged and the previous model is replaced by that averaged model.

        In case a balancing request is sent, this info is logged and a method is called ('answerParameterRequest') that handles the answering of such a request

        Parameters
        ----------
        default parameters from RabbitMQ for callback; body contains the message itself

        Returns
        -------
        None

        '''

        self.info('Got message in the worker queue')
        #self.info('STARTTIME_onMessageReceived: '+str(time.time()))

        if 'newModel' in routing_key:
            body_size = sys.getsizeof(body)
            self._communicator.learningLogger.logSendModelMessage(exchange, routing_key, body_size, 'receive', self.getIdentifier())
            self.info("The learner received initial setup or averaged model, with or without reference model")
            message = pickle.loads(body)
            param = message['param']
            flags = message['flags']
            self._learner.setModel(param, flags)
        if 'request' in routing_key:
            body_size = 0
            self._communicator.learningLogger.logBalancingRequestMessage(exchange, routing_key,body_size, 'receive', self.getIdentifier())
            self.info("Coordinator asks for parameters to balance violation")
            self._learner.answerParameterRequest()
        #self.info('ENDTIME_onMessageReceived: '+str(time.time()))

    def retrieveMessages(self):
        '''
        checks pipes for new in coming messages and acts in case that a messages arrived. Since messages arriving from
        communicator are just those arriving at the communicator, we receive one type of message here. It similar for
        the data scheduler.

        Exceptions
        ----------
        ValueError
            in case that the received message doesn't fit with the expected type
        '''
        if self._communicatorConnection.poll():
            #self.info('STARTTIME_retrieveMessages_communicatorConnection: '+str(time.time()))
            recvObj     = self._communicatorConnection.recv()
            #recvObj = loads(recvObj)

            if not isinstance(recvObj,tuple):
                raise ValueError("worder received recvObj is not a tuple")
            elif not len(recvObj) == 3:
                raise ValueError("worder received recvObj, which has length of  different from 4")

            routing_key, exchange, body = recvObj
            self.onMessageReceived(routing_key, exchange, body)
            #self.info('ENDTIME_retrieveMessages_communicatorConnection: '+str(time.time()))


        if self._dataSourceConnection.poll():
            recvObj     = self._dataSourceConnection.recv()
            value       = loads(recvObj)

            self._dataBuffer.append(value)

    def _setConnectionsToComponents(self):
        '''

        distributes the transmitters and receiver connections over the different processes such that an inter process
        communication can take place.

        Exceptions
        ----------
        AttributeError
            in case if either no dataScheduler, no communicator or no learner is set

        '''

        if self._dataScheduler is None:
            self.error("DataScheduler not set!")
            raise AttributeError("DataScheduler not set!")

        if self._communicator is None:
            self.error("Communicator not set!")
            raise AttributeError("Communicator not set!")

        if self._learner is None:
            self.error("Learner not set!")
            raise AttributeError("Learner not set!")

        self._communicator.setConnections   (workerConnection       = self._communicatorConnections[1])
        self._dataScheduler.setConnections  (workerConnection       = self._dataSourceConnections[1])

    def run(self):
        '''

        Configures and starts data scheduler and communicator of the worker.

        Requests initial model from the coordinator.

        Continuously transfers training data points from data buffer to learner.
        The actual operation logic of the worker

        Returns
        -------

        Exception
        ---------
        AttributeError
            In case that at least one of the necessary modules DataScheduler, Communicator or Learner is not set
            In case that at least on of the necessary modules DataScheduler, communicator or Learner is not set or in
            case that the connection from dataScheduler or to the communicator aren't set.
        '''

        if self._dataScheduler is None:
            self.error("DataScheduler not set!")
            raise AttributeError("DataScheduler not set!")

        if self._communicator is None:
            self.error("Communicator not set!")
            raise AttributeError("Communicator not set!")

        if self._learner is None:
            self.error("Learner not set!")
            raise AttributeError("Learner not set!")

        self._learner.setCommunicator(self._communicator)

        # dataScheduler is for individual setup of giving data to the worker
        #  it is running in its own process since the data is constantly generated, independent from the learner
        self._dataScheduler.daemon = True

        # communicator runs in thread to consume the queue of the worker
        self._communicator.initiate(exchange = self._communicator._exchangeNodes, topics = ["#."+self.getIdentifier()+".#", "#."+self.getIdentifier()])
        self._communicator.daemon = True

        self._setConnectionsToComponents()

        self._dataScheduler.start()
        self._communicator.start()

        if (self._communicatorConnection == None) or (self._dataSourceConnection == None):
            raise AttributeError("either communicatorConnection or dataSourceConnection was not set properly at the worker!")

        # initializing of consumer takes time... 
        time.sleep(5)
        # only now we should reuqest for initial model - or we will not be able to receive the answer
        self._learner.requestInitialModel()

        while True:
            self.retrieveMessages()
            #print("retrieved messages ******************************************")
            if len(self._dataBuffer) > 0:
                #print("buffer is not empty ", len(self._dataBuffer), "**************************************************")
                #print("learner can train ", self._learner.canObtainData(), "************************************************")
                if self._learner.canObtainData():
                    self._learner.obtainData(self._dataBuffer[0])
                    del(self._dataBuffer[0])

        self._dataScheduler.join()
        self._communicator.join()
