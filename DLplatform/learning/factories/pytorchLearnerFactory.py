from DLplatform.learning.deeplearning.pyTorchNN import PyTorchNN

import numpy as np
import random

import torch.nn as nn
import torch
import torch.nn.functional as F
import torch.optim as optim
import torch.nn.init as init
from DLplatform.learning.factories import LearnerFactory

class PytorchLearnerFactory(LearnerFactory):
    
    def __init__(self, network : nn.Module, updateRule, learningRate, lossFunction, batchSize, learningParams = None, syncPeriod = 1):
        self.network        = network
        self.updateRule     = updateRule
        self.learningRate   = learningRate
        self.learningParams = learningParams
        self.lossFunction   = lossFunction
        self.batchSize      = batchSize
        self.syncPeriod     = syncPeriod
        
    def getLearner(self):
        device = torch.device("cuda:0" if torch.cuda.is_available() else None)
        if device is None:
            mode = 'cpu'
        else:
            mode = 'gpu'
        torchNetwork = self.network.cuda()
        learner = PyTorchNN(batchSize=self.batchSize, syncPeriod=self.syncPeriod, mode=mode, device=device)
        learner.setCore(torchNetwork)
        learner.setLoss(self.lossFunction)
        learner.setUpdateRule(self.updateRule, self.learningRate, **self.learningParams)
        return learner

    def getLearnerOnDevice(self, mode, device):
        torchNetwork = self.network
        if mode == 'gpu':
            torchNetwork = torchNetwork.cuda(device)
        learner = PyTorchNN(batchSize=self.batchSize, syncPeriod=self.syncPeriod, mode=mode, device=device)
        learner.setCore(torchNetwork)
        learner.setLoss(self.lossFunction)
        learner.setUpdateRule(self.updateRule, self.learningRate, **self.learningParams)
        return learner

    def __str__(self):
        return "PyTorch Learner, network " + str(self.network) + ", update rule " + self.updateRule +", learning rate " + str(self.learningRate) + ", loss function " + self.lossFunction + ", batch size " + str(self.batchSize) + ", sync period " + str(self.syncPeriod)


