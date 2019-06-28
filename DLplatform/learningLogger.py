import os
import time, pickle
from DLplatform.parameters import Parameters
from typing import List
import numpy as np

class LearningLogger():
    '''
    Class with all the logging files creation needed for 
    monitoring of the learning process. All the logs are 
    written along with the current timestamp in milliseconds.
    '''
    # log files names are hardcoded
    _learnerLossFile = 'losses.txt'
    _learnerPredLabelFile = 'predictions.txt'
    _learnerViolationsFile = 'violations.txt'
    _learnerBalancingFile = 'balancing.txt'
    _learnerRegistrationsFile = 'registrations.txt'
    _learnerBalancingRequestFile = 'balancing_requests.txt'
    _learnerSendModelFile = 'send_model.txt'
    
    def __init__(self, path: str, id, level='NORMAL'):
        '''
        Initializes logging level and the path to the logging files
        Logging level defines for example if all the averaged models 
        are saved.

        Parameters
        ----------
        path to the logging files
        id defines the folder that the files will be saved inside the path
            for example 'coordinator', 'worker0', etc.
        level of the logging
        '''
        self._logLevel = level
        self._path = path
        self._id = str(id)

        self._logpath = os.path.join(self._path, self._id)
        if not os.path.isdir(self._logpath):
            os.mkdir(self._logpath)

    def logLearnerLoss(self, lossValue: float):
        '''
        Logs loss suffered by a worker

        Parameters
        ----------
        lossValue
        '''
        logFilePath = os.path.join(self._logpath, self._learnerLossFile)
        with open(logFilePath, 'a') as output:
            output.write('%.3f\t%.8f\n' % (time.time(), lossValue))

    def logPredictionsLabels(self, predictions: list, labels: list):
        '''
        Logs predictions of the worker along with the labels
        Allows to calculate accuracy afterwards.

        Parameters
        ----------
        predictions - list of predictions made by a worker
        labels - true labels corresponding to predictions
        '''
        logFilePath = os.path.join(self._logpath, self._learnerPredLabelFile)
        with open(logFilePath, 'a') as output:
            for i in range(len(predictions)):
                if isinstance(labels[i], int) and isinstance(predictions[i], int):
                    output.write('%.3f\t%s\t%s\n' % (time.time(), str(predictions[i]), str(labels[i])))
                elif isinstance(labels[i], float) and isinstance(predictions[i], float):
                    output.write('%.3f\t%s\t%s\n' % (time.time(), str(predictions[i]), str(labels[i])))
                elif isinstance(labels[i], int) and not isinstance(predictions[i], int):
                    output.write('%.3f\t%s\t%s\n' % (time.time(), ','.join(map(str, predictions[i])), str(labels[i])))
                else:
                    output.write('%.3f\t%s\t%s\n' % (time.time(),
                        ','.join(map(str, predictions[i])), ','.join(map(str, labels[i]))))

    def logViolation(self, distance: float, delta: float, localConditionHolds: bool):
        '''
        Logs violations along with violation distance and delta for dynamic synchronization

        Parameters
        ----------
        distance
        delta
        localConditionHolds - defines if violation is observed, opposite value is logged
            for intuitive understandability of the logs
            if log level is DEBUG all the checks are written
            otherwise only violation (i.e. when it is False) is logged
        '''
        logFilePath = os.path.join(self._logpath, self._learnerViolationsFile)
        with open(logFilePath, 'a') as output:
            if self._logLevel == 'DEBUG' or not localConditionHolds:
                if delta is None:
                    output.write('%.3f\t%i\n' % (time.time(), not localConditionHolds))
                else:
                    output.write('%.3f\t%i\t%s\t%4.f\n' % (time.time(), not localConditionHolds, str(distance), delta))

    def logBalancing(self, flags: dict, violationNodes: list, balancingSet: list):
        '''
        Logs balancing that happenned on coordinator side
        The nodes that reported violation and the nodes that finally took 
        part in the balancing process are written together with a flag if the 
        synchronization was full.

        Parameters
        ----------
        flags - returned flags from synchronization
        violationNodes - nodes in violation
        balancingSet - nodes that performed balancing
        '''
        logFilePath = os.path.join(self._logpath, self._learnerBalancingFile)
        if flags.get('setReference') is None:
            fullSync = False
        else:
            fullSync = flags['setReference']
        with open(logFilePath, 'a') as output:
            output.write('%.3f\t%i\t%s\t%s\n' % (time.time(), fullSync,
                ','.join(map(str, violationNodes)), ','.join(map(str, balancingSet))))

    def logAveragedModel(self, nodes : List[int], params: Parameters, flags:dict):
        '''
        Logs averaged model, i.e., saves the parameters of an averaged model
        If loglevel is DEBUG the models are saved with timestamp, otherwise
        one and the same file is overwritten.

        Parameters
        ----------
        params - weights of an averaged model
        '''
        if "nosync" in flags:
            if self._logLevel == 'DEBUG':
                filename = 'averagedState_' + str(time.time())  + '_node_'+str(nodes[0])
                self.logModel(filename = filename, params = params)
            else:
                filename = 'currentAveragedState_node_'+str(nodes[0])
                self.logModel(filename = filename, params = params)
        else:
            if self._logLevel == 'DEBUG':
                filename = 'averagedState_' + str(time.time())
                self.logModel(filename = filename, params = params)
                #np.save(os.path.join(self._logpath, modelName), params.get())
            else:
                filename = 'currentAveragedState'
                self.logModel(filename = filename, params = params)
                #np.save(os.path.join(self._logpath, 'currentAveragedWeights'), params.get())

    def logModel(self, filename : str, params: Parameters):
        '''
        Logs a model, i.e., saves the parameters of a model

        Parameters
        ----------
        filename - what name contains the model parameters
        params - weights of an averaged model
        '''
        pickle.dump(params, open(os.path.join(self._logpath, filename), 'wb'))

    '''
    All the messages are logged with exchange used, topic used, identifier of the node if
    applicable and direction - was it sent or received. Ideally each send log line will
    correspond to one receive log line.
    '''
    def logViolationMessage(self, exchange: str, topic: str, identifier, message_size: int, direction: str):
        '''
        Logs violation message

        Parameters
        ----------
        exchange
        topic
        identifier of the worker that sent the violation
        size of the message
        direction
        '''
        logFilePath = os.path.join(self._logpath, self._learnerViolationsFile)


        with open(logFilePath, 'a') as output:
            output.write('%.3f\t%s\t%s\t%s\t%s\t%s\n' % (time.time(), 
                exchange, topic, str(identifier), str(message_size), direction))

    def logRegistrationMessage(self, exchange: str, topic: str, identifier, message_size: int, direction: str):
        '''
        Logs registration message

        Parameters
        ----------
        exchange
        topic
        identifier of the worker that is registered
        direction
        '''
        logFilePath = os.path.join(self._logpath, self._learnerRegistrationsFile)
        with open(logFilePath, 'a') as output:
            output.write('%.3f\t%s\t%s\t%s\t%s\t%s\n' % (time.time(), 
                exchange, topic, str(identifier), str(message_size), direction))

    def logDeregistrationMessage(self, exchange: str, topic: str, identifier, message_size: int, direction: str):
        '''
        Logs deregistration message

        Parameters
        ----------
        exchange
        topic
        identifier of the worker that is deregistered
        direction
        '''
        logFilePath = os.path.join(self._logpath, self._learnerRegistrationsFile)
        with open(logFilePath, 'a') as output:
            output.write('%.3f\t%s\t%s\t%s\t%s\t%s\n' % (time.time(), 
                exchange, topic, str(identifier), str(message_size), direction))

    def logBalancingMessage(self, exchange: str, topic: str, identifier, message_size: int, direction: str):
        '''
        Logs balancing message

        Parameters
        ----------
        exchange
        topic
        identifier of the worker that is sending the parameters for balancing process
        direction
        '''
        logFilePath = os.path.join(self._logpath, self._learnerBalancingFile)
        with open(logFilePath, 'a') as output:
            output.write('%.3f\t%s\t%s\t%s\t%s\t%s\n' % (time.time(), 
                exchange, topic, str(identifier), str(message_size), direction))

    def logBalancingRequestMessage(self, exchange: str, topic: str, message_size: int, direction: str, workerId = None):
        '''
        Logs balancing request message

        Parameters
        ----------
        exchange
        topic
        workerId of the worker that is requested. When the message is received we log the workerId,
            otherwise it is in the topic
        direction
        '''
        logFilePath = os.path.join(self._logpath, self._learnerBalancingRequestFile)
        with open(logFilePath, 'a') as output:
            if workerId is None:
                output.write('%.3f\t%s\t%s\t%s\t%s\n' % (time.time(), exchange, topic, str(message_size), direction))
            else:
                output.write('%.3f\t%s\t%s\t%s\t%s\t%s\n' % (time.time(), 
                    exchange, topic, str(message_size), direction, workerId))
        
    def logSendModelMessage(self, exchange: str, topic: str, message_size: int, direction: str, workerId = None):
        '''
        Logs message of sending averaged model after balancing

        Parameters
        ----------
        exchange
        topic
        workerId of the worker that is getting the model
        direction
        '''
        logFilePath = os.path.join(self._logpath, self._learnerSendModelFile)
        with open(logFilePath, 'a') as output:    
            if workerId is None:
                output.write('%.3f\t%s\t%s\t%s\t%s\n' % (time.time(), exchange, topic, str(message_size), direction))
            else:
                output.write('%.3f\t%s\t%s\t%s\t%s\t%s\n' % (time.time(), exchange, topic, str(message_size), direction, workerId))

