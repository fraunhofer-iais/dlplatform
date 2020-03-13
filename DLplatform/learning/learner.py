
from DLplatform.baseClass import baseClass
from DLplatform.parameters import Parameters
from DLplatform.communicating import Communicator

from abc import ABCMeta
from typing import List
import time
import sys


class Learner(baseClass):
    '''
    Abstract class defining the structure of a IncrementalLearner. This includes batch and online learners.

    '''
    __metaclass__ = ABCMeta
    
    def __init__(self, name = "IncrementalLearner", identifier = ""):
        '''
        Initialize all the parameters with initial values and base class with name IncrementalLearner
        '''
        
        baseClass.__init__(self, name = name)
        self._identifier                = identifier
        self._isTraining                = False
        self._learningLogger            = None
        self._communicator              = None
        self._synchronizer              = None
        
    def setIdentifier(self, identifier):
        '''
        Setter for identifier

        Parameters
        ----------
        identifier - can be string or integer - anything for defining the IncrementalLearner unquely

        Returns
        -------
        None

        '''
        self._identifier = identifier
        
    def setCommunicator(self, com: Communicator):
        '''
        Setter for communicator of the learner

        Parameters
        ----------
        com - instance of Communicator class

        Exception
        -------
        ValueError
            in case that com is not a Communicator
        '''

        if not isinstance(com, Communicator):
            error_text = "The argument func is not of type" + str(Communicator) + "it is of type " + str(type(com))
            self.error(error_text)
            raise ValueError(error_text)

        self._communicator = com
        
    def setLearningLogger(self, logger):
        '''
        Setter for Learning Logger

        Parameters
        ----------
        logger - instance of LearningLogger class

        Returns
        -------
        None

        '''
        self._learningLogger = logger
        
    def stopExecution(self):
        if self._communicator is None:
            self.error("No communicator is set")
            raise AttributeError("No communicator is set")

        self.info("Stopping criterion was met, sending suicide note to coordinator")
        self._communicator.sendDeregistration(self._identifier, self.getParameters())
        sys.exit()
        
    def setModel(self, param : Parameters, flags: dict):
        '''
        Function for updating the learner parameters either when registred or when 
        balancing was performed and coordinator returned a new averaged model
        In case when full synchronization was performed the reference model
        is also set.

        Parameters
        ----------
        param - parameters received from coordinator
        setReference - should the reference model be updated

        Returns
        -------
        None

        Exception
        ---------
        ValueError
            in case that param is not of type Parameters
        '''
        #self.info('STARTTIME_setModel: '+str(time.time()))
        if not isinstance(param, Parameters):
            error_text = "The argument param is not of type" + str(Parameters) + "it is of type " + str(type(param))
            self.error(error_text)
            raise ValueError(error_text)

        self.info("received a model update")
        self.setParameters(param)
        self.info("replacing current model with updated one")
        self._waitingForAModel = False
        if "setReference" in flags and flags["setReference"] == True:
            self._referenceModel = param
        #self.info('ENDTIME_setModel: '+str(time.time()))
    
    def answerParameterRequest(self):
        '''
        Function called when balancing request from coordinator is received
        Switches the state of the learner to waiting, i.e., training is not
        happening and calls communicator method for sending the current parameters.
        Will not return parameters until the training is happening. Will not
        return params if waiting for the updated model already.

        Returns
        -------
        None

        Exception
        ---------
        AttributeError
            in case communicator is not set
        '''

        #self.info('STARTTIME_answerBalancingRequest: '+str(time.time()))
        if self._communicator is None:
            self.error("No communicator is set")
            raise AttributeError("No communicator is set")

        self.info("received a request for parameters")
        while self._isTraining:
            time.sleep(1)
        # in the case we are already waiting for a new model we sent a violation report - so we do not need to send parameters again
        if not self._waitingForAModel:
            self._waitingForAModel = True
            self._communicator.sendParameters(self._identifier, self.getParameters())
        #self.info('ENDTIME_answerBalancingRequest: '+str(time.time()))
    
    def setStoppingCriterion(self, stoppingCriterion):
        self._stoppingCriterion = stoppingCriterion

    def setSynchronizer(self, synchronizer):
        self._synchronizer = synchronizer
        
    def requestInitialModel(self):
        '''
        Wrap function over calling communicator in order to send registration request
        Called only once when model is initialized and should be added to the system.
        Requesting the initial parameters results in staying in waiting state, so the
        learner does not accept any data and does not train, as well as does not return its
        parameters on balancing request.

        Returns
        -------
        None

        Exception
        ---------
        AttributeError
            in case the communicator is not initialized

        '''

        if self._communicator is None:
            self.error("No communicator is set")
            raise AttributeError("No communicator is set")

        self.info("Requesting the initial/current model")
        self._communicator.sendRegistration(self._identifier, self.getParameters())
        self._waitingForAModel = True
        self._readyToTrain = False
        
    def reportViolation(self):
        '''
        Wrap function over calling communicator in order to send violation message
        Called as a result of checking local condition if it is violated

        Returns
        -------
        None

        Exception
        ---------
        AttributeError
            in case the communicator is not initialized

        '''

        #self.info('STARTTIME_reportViolation: '+str(time.time()))
        if self._communicator is None:
            self.error("No communicator is set")
            raise AttributeError("No communicator is set")

        self.info("Reporting a violation")
        self._communicator.sendViolation(self._identifier, self.getParameters())
        self._waitingForAModel = True
        #self.info('ENDTIME_reportViolation: '+str(time.time()))
                    
    def setParameters(self, param : Parameters):
        '''
        Assign new parameters to the learner
        Method called by setModel, implemented in the specific implementation
        of a learner.

        Parameters
        ----------
        param - parameters to assign

        '''

        raise NotImplementedError

    def getParameters(self) -> Parameters:
        '''
        Get current parameters of a learner
        Implemented in a specific implementation of a learner

        Returns
        -------
        Parameters - current parameters of a learner

        '''

        raise NotImplementedError

class IncrementalLearner(Learner):
    '''
    Abstract class defining the structure of a IncrementalLearner that contains the core model and trains it on the incoming data.
    IncrementalLearner is a part of Worker that performs all the actions concerned with training, getting and setting parameters,
    checking violations\times to synchronize.

    '''

    __metaclass__ = ABCMeta

    def __init__(self, batchSize : int, syncPeriod : int, name = "IncrementalLearner", identifier = ""):
        '''
        Initialize all the parameters with initial values and base class with name IncrementalLearner

        Parameters
        ----------
        batchSize - defines the training batchSize, i.e. amount of examples needed to perform one update of the parameters
        syncPeriod - defines the periodicity of local condition checking. For periodic synchronization it means that 
            every syncPeriod examples synchronization will be performed. For dynamic synchronization it means that
            every syncPeriod examples local divergence will be checked.
        identifier - can be set from initializer, but generally set from the setter. It is equal to the identifier of the
            Worker that contains this IncrementalLearner

        Returns
        -------
        None

        '''

        Learner.__init__(self, name, identifier)
        self._batchSize                 = batchSize
        self._syncPeriod                = syncPeriod
        

        self._referenceModel            = None

        self._waitingForAModel          = False
        self._trainingBatch             = []
        self._syncCounter		        = 0
        self._seenExamples              = 0



    def obtainData(self, example: tuple):
        '''
        Main learner function initiating training and violations checking
        In case there are not enough examples it is just added up to the current batch
        In case if we have enough training samples in the buffer for the batch training
        step we start training. Then local condition is checked and in case there is a 
        violation the message to coordinator is sent. While training and checking 
        condition is happening the flag isTraining set to True, so the model parameters
        cannot be requested.

        Parameters
        ----------
        example - tuple consisting of an example and its label

        Returns
        -------
        None

        '''
        #self.info('STARTTIME_obtainData: '+str(time.time()))
        self._trainingBatch.append(example)
        if len(self._trainingBatch) >= self._batchSize:
            currentBatch = self._trainingBatch[:self._batchSize]
            self._trainingBatch = self._trainingBatch[self._batchSize:]
            self._isTraining = True
            metrics = self.update(currentBatch)
            self._seenExamples += len(currentBatch)
            # first element of metrics is loss value
            self._learningLogger.logLearnerLoss(metrics[0])
            # second element of metrics is an array with predictions
            self._learningLogger.logPredictionsLabels(metrics[1], [t[1] for t in currentBatch])
            #self.info('STARTTIME_checkLocalCondition: '+str(time.time()))
            localEvaluateMsg, localConditionHolds = self.checkLocalConditionHolds()
            #self.info('ENDTIME_checkLocalCondition: '+str(time.time()))
            self._learningLogger.logViolation(localEvaluateMsg, localConditionHolds)
            if not self._stoppingCriterion is None and self._stoppingCriterion(self._seenExamples, time.time()):
                self.stopExecution()
            if not localConditionHolds:
                self.reportViolation()
            # @TODO where does it make more sense - before or after checking local condition
            self._isTraining = False
        #self.info('ENDTIME_obtainData: '+str(time.time()))


    def canObtainData(self) -> bool:
        '''
        Obtains the state of the learner
        Requested by the worker before sending the next example for training.
        Returns False if the parameters should be updated or the model is 
        training currently

        Returns
        -------
        boolean value, defining allowance to accept the next training example

        '''
        return not self._waitingForAModel and not self._isTraining



    def checkLocalConditionHolds(self) -> (float, bool):
        '''
        Checks local condition for violation
        Should be implemented in specific implementation of a learner.

        Returns
        -------
        float - divergence in a case when we check it for dynamic protocols
        bool - if violation should be sent
        '''

        raise NotImplementedError


    def update(self, data: List) -> List:
        '''
        Training step
        Should be implemented in specific learner implementation.

        Parameters
        ----------
        data - training batch

        Returns
        -------
        list - first element is loss suffered on this training step
                second element are predictions for the batch

        '''

        raise NotImplementedError
    
class BatchLearner(Learner):
    def __init__(self, name = "BatchLearner", identifier = ""):
        Learner.__init__(self, name, identifier)
        self._isInitialized             = True
        self._parametersRequested       = False
        self._waitingForAModel          = False
        self._stop                      = False
        self._trainingBatch             = []
        self._seenExamples              = 0
        
    def canObtainData(self) -> bool:
        '''
        Obtains the state of the learner
        Requested by the worker before sending the training data.

        Returns
        -------
        boolean value, defining allowance to accept training data

        '''
        if self._stop and not self._waitingForAModel: #as soon as the stopping criterion is met and the aggregate model is set, the learner is stopped
            self.stopExecution()
        return self._isInitialized and not self._isTraining and not self._stop and not self._waitingForAModel
    
    def obtainData(self, example: tuple):
        '''
        Main learner function initiating training and violations checking
        In case there are not enough examples it is just added up to the current batch
        In case if we have enough training samples in the buffer for the batch training
        step we start training. Then local condition is checked and in case there is a 
        violation the message to coordinator is sent. While training and checking 
        condition is happening the flag isTraining set to True, so the model parameters
        cannot be requested.

        Parameters
        ----------
        example - tuple consisting of an example and its label

        Returns
        -------
        None

        '''
        #self.info('STARTTIME_obtainData: '+str(time.time()))
        self._trainingBatch.append(example)
        self._seenExamples = len(self._trainingBatch)
        if not self._stoppingCriterion is None and self._stoppingCriterion(self._seenExamples, time.time()):
            self._parametersRequested = False #the new parameters after training have not yet been sent
            self._isTraining = True
            metrics = self.train(self._trainingBatch)
            # first element of metrics is loss value
            self._learningLogger.logLearnerLoss(metrics[0])
            # second element of metrics is an array with predictions
            self._learningLogger.logPredictionsLabels(metrics[1], [t[1] for t in self._trainingBatch])
            #batch learners report a violation whenever they finished training. 
            #The model is send once, aggregated and redistributed, then the learner stops.
            self.reportViolation()
            self._stop = True
            self._isTraining = False
            
            
    def train(self, data: List) -> List:
        '''
        Training
        Should be implemented in specific learner implementation.

        Parameters
        ----------
        data - training batch

        Returns
        -------
        list - first element is loss suffered on this training step
                second element are predictions for the batch

        '''

        raise NotImplementedError    
        
    def answerParameterRequest(self):
        '''
        This function extends the super class "Learner"'s answerParameterRequest to include a stopping condition. 
        If in a BatchLearner a single batch has been processed for training and the parameters have been requested,
        then the execution can be stopped.
        '''
        Learner.answerParameterRequest(self)
        self._parametersRequested = True
        if self._stop and not self._waitingForAModel:
            self.stopExecution()

