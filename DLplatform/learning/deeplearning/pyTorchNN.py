from DLplatform.learning import IncrementalLearner
from DLplatform.parameters.pyTorchNNParameters import PyTorchNNParameters

import numpy as np
from typing import List
import torch
import torch.nn as nn
import torch.optim as optim
from collections import OrderedDict

class PyTorchNN(IncrementalLearner):
    def __init__(self, batchSize, syncPeriod, delta, name = "PyTorchNN"):
        IncrementalLearner.__init__(self, batchSize = batchSize, syncPeriod = syncPeriod, delta = delta, name = name)

        self._core          = None
        self._flattenReferenceParams    = None

    def setCore(self, network):
        self._core = network

    def setModel(self, param: PyTorchNNParameters, setReference: bool):
        super(PyTorchNN, self).setModel(param, setReference)
        
        if setReference:
            self._flattenReferenceParams = self._flattenParameters(param)

    def setLoss(self, lossFunction):
        self._loss = eval("nn." + lossFunction + "()")

    def setUpdateRule(self, updateRule, learningRate, **kwargs):
        additional_params = ""
        for k in kwargs:
            additional_params += ", " + k  + "=" + str(kwargs.get(k))
        self._updateRule = eval("optim." + updateRule + "(self._core.parameters(), lr=" + str(learningRate) + additional_params + ")")

    def checkLocalConditionHolds(self) -> (float, bool):
        '''

        Returns
        -------
        bool
        '''
        localConditionHolds = True
        currentDivergence = None
        self._syncCounter += 1
        if self._syncCounter == self._syncPeriod:
            if not self._delta is None:
                currentDivergence = self.calculateCurrentDivergence()
                localConditionHolds = currentDivergence <= self._delta
            else:
                localConditionHolds = False
            self._syncCounter = 0

        return currentDivergence, localConditionHolds

    def update(self, data: List) -> List:
        '''

        Parameters
        ----------
        data

        Returns
        -------

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
       
        example = np.asarray([record[0] for record in data])
        label = np.asarray([record[1] for record in data])
        self._updateRule.zero_grad()   # zero the gradient buffers
        output = self._core(torch.cuda.FloatTensor(example))
        if type(self._loss) is nn.MSELoss or type(self._loss) is nn.L1Loss:
            loss = self._loss(output, torch.cuda.FloatTensor(label))
        else:
            loss = self._loss(output, torch.cuda.LongTensor(label))
        loss.backward()
        self._updateRule.step()    # Does the update
        return [loss.data.cpu().numpy(), output.data.cpu().numpy()]

    def setParameters(self, param : PyTorchNNParameters):
        '''

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

        if not isinstance(param, PyTorchNNParameters):
            error_text = "The argument param is not of type" + str(PyTorchNNParameters) + "it is of type " + str(type(param))
            self.error(error_text)
            raise ValueError(error_text)

        state_dict = OrderedDict()
        #print(param.get()['layer3.5.bn3.num_batches_tracked'])
        #print(param.get()['layer3.5.bn3.num_batches_tracked'].shape)
        for k,v in param.get().items():
            if v.shape == ():
                #print(torch.tensor(v))
                state_dict[k] = torch.tensor(v)
            else:
                state_dict[k] = torch.cuda.FloatTensor(v)
        self._core.load_state_dict(state_dict)

    def getParameters(self) -> PyTorchNNParameters:
        '''

        Returns
        -------
        Parameters

        '''
        #print("***************")
        #print(self._core.state_dict()['layer3.5.bn3.num_batches_tracked'])
        #print(self._core.state_dict()['layer3.5.bn3.num_batches_tracked'].data.cpu().numpy())

        state_dict = OrderedDict()
        for k, v in self._core.state_dict().items():
            state_dict[k] = v.data.cpu().numpy()
        return PyTorchNNParameters(state_dict)

    def calculateCurrentDivergence(self):
        flattenCoreParams = self._flattenParameters(self.getParameters())
        return np.linalg.norm(flattenCoreParams - self._flattenReferenceParams)

    def _flattenParameters(self, param):
        flatParam = []
        for k,v in param.get().items():
            flatParam += np.ravel(v).tolist()
        return np.asarray(flatParam)
