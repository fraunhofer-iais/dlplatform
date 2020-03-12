from DLplatform.learning import IncrementalLearner
from DLplatform.parameters.pyTorchNNParameters import PyTorchNNParameters

import numpy as np
from typing import List
import torch
import torch.nn as nn
import torch.optim as optim
from collections import OrderedDict

class PyTorchNN(IncrementalLearner):
    def __init__(self, batchSize, syncPeriod, delta, mode, device, name = "PyTorchNN"):
        IncrementalLearner.__init__(self, batchSize = batchSize, syncPeriod = syncPeriod, delta = delta, name = name)

        self._core          		= None
        self._flattenReferenceParams    = None
        self._mode			= mode
        self._device			= device

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
        self._syncCounter += 1
        if self._syncCounter == self._syncPeriod:
            msg, localConditionHolds = self._synchronizer.evaluateLocal(self.getParameters().getList(), self._flattenReferenceParams)
            self._syncCounter = 0

        return msg, localConditionHolds

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
        if self._mode == 'gpu':
            exampleTensor = torch.cuda.FloatTensor(example, device=self._device)
            if type(self._loss) is nn.MSELoss or type(self._loss) is nn.L1Loss:
                labelTensor = torch.cuda.FloatTensor(label, device=self._device)
            else:
                labelTensor = torch.cuda.LongTensor(label, device=self._device)
        else:
            exampleTensor = torch.FloatTensor(example)
            if type(self._loss) is nn.MSELoss or type(self._loss) is nn.L1Loss:
                labelTensor = torch.FloatTensor(label)
            else:
                labelTensor = torch.LongTensor(label)
        output = self._core(exampleTensor)
        loss = self._loss(output, labelTensor)
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
        for k,v in param.get().items():
            if self._mode == 'gpu':
                if v.shape == ():
                    state_dict[k] = torch.tensor(v, device=self._device)
                else:
                    state_dict[k] = torch.cuda.FloatTensor(v, device=self._device)
            else:
                if v.shape == ():
                    state_dict[k] = torch.tensor(v)
                else:
                    state_dict[k] = torch.FloatTensor(v)
        self._core.load_state_dict(state_dict)

    def getParameters(self) -> PyTorchNNParameters:
        '''

        Returns
        -------
        Parameters

        '''
        state_dict = OrderedDict()
        for k, v in self._core.state_dict().items():
            state_dict[k] = v.data.cpu().numpy()
        return PyTorchNNParameters(state_dict)

