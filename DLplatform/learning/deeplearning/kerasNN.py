from DLplatform.learning import IncrementalLearner
from DLplatform.parameters.kerasNNParameters import KerasNNParameters

import numpy as np
import time
from typing import List

class KerasNN(IncrementalLearner):
    def __init__(self, batchSize, syncPeriod, delta, session, name = "KerasNN"):
        IncrementalLearner.__init__(self, batchSize = batchSize, syncPeriod = syncPeriod, delta = delta, name = name)

        self._core          = None

        self._flattenReferenceParams    = None
        self._session = session

    def setCore(self, network):
        self._core = network

    def setModel(self, param: KerasNNParameters, setReference: bool):
        super(KerasNN, self).setModel(param, setReference)
        
        #self.info('STARTTIME_setReference: '+str(time.time()))
        if setReference:
            self._flattenReferenceParams = self._flattenParameters(param)
        #self.info('ENDTIME_setReference: '+str(time.time()))

    def checkLocalConditionHolds(self) -> (float, bool):
        '''

        Calculates the divergence of the local model from the reference model (currentDivergence) and compares it with the pre-defined divergence threshold (_delta)

        Returns
        -------
        bool

        '''
        localConditionHolds = True
        self._syncCounter += 1
        if self._syncCounter == self._syncPeriod:
            msg, localConditionHolds = self._synchronizer.evaluateLocal(self.getParameters().getList(), self._flattenReferenceParams)
            self._syncCounter = 0

        return msg, localConditionHolds

    def update(self, data: List) -> List:
        '''

        Calls the keras method "train_on_batch" that performs a single gradient update of the model based on batch "data" and returns performance of that updated model on "data"

        Parameters
        ----------
        data

        Returns
        -------
        scalar training loss

        Exception
        ---------
        AttributeError
            in case core is not set
        ValueError
            in case that data is not an numpy array
        '''
        if self._core is None:
            self.error("No core is set")
            raise AttributeError("No core is set")

        if not isinstance(data, List):
            error_text = "The argument data is not of type" + str(List) + "it is of type " + str(type(data))
            self.error(error_text)
            raise ValueError(error_text)

        #self.info('STARTTIME_train_on_batch: '+str(time.time()))
        with self._session.as_default():
            with self._session.graph.as_default():
                metrics = self._core.train_on_batch(np.asarray([record[0] for record in data]), np.asarray([record[1] for record in data]))
        #self.info('ENDTIME_train_on_batch: '+str(time.time()))
        return metrics

    def setParameters(self, param : KerasNNParameters):
        '''

        Replace the current values of the model parameters with the values of "param"

        Parameters
        ----------
        param

        Returns
        -------

        Exception
        ---------
        ValueError
            in case that param is not of type Parameters
        '''

        if not isinstance(param, KerasNNParameters):
            error_text = "The argument param is not of type" + str(KerasNNParameters) + "it is of type " + str(type(param))
            self.error(error_text)
            raise ValueError(error_text)

        with self._session.as_default():
            with self._session.graph.as_default():
                self._core.set_weights(param.get())

    def getParameters(self) -> KerasNNParameters:
        '''

        Takes the current model parameters and hands them to a KerasNNParameters object which is returned

        Returns
        -------
        Parameters

        '''

        with self._session.as_default():
            with self._session.graph.as_default():
                return KerasNNParameters(self._core.get_weights())
