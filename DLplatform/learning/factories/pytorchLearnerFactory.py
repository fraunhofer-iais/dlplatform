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
    
    def __init__(self, network : nn.Module, updateRule, learningRate, lossFunction, batchSize, learningParams = None, syncPeriod = 1, delta = None):
        self.network        = network
        self.updateRule     = updateRule
        self.learningRate   = learningRate
        self.learningParams = learningParams
        self.lossFunction   = lossFunction
        self.batchSize      = batchSize
        self.syncPeriod     = syncPeriod
        self.delta          = delta
        
    def getLearner(self):
        torchNetwork = self.network.cuda()
        learner = PyTorchNN(batchSize=self.batchSize, syncPeriod=self.syncPeriod, delta=self.delta)
        learner.setCore(torchNetwork)
        learner.setLoss(self.lossFunction)
        learner.setUpdateRule(self.updateRule, self.learningRate, **self.learningParams)
        return learner

    def __str__(self):
        return "PyTorch Learner, network " + str(self.network) + ", update rule " + self.updateRule +", learning rate " + str(self.learningRate) + ", loss function " + self.lossFunction + ", batch size " + str(self.batchSize) + ", sync period " + str(self.syncPeriod) + ", delta " + str(self.delta)


