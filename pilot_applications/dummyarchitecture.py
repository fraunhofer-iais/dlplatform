'''
created on 20.04.2018

author twirtz
'''

import threading
import numpy as np
import time

class Model:
    pass

class Commuincator(threading.Thread):


    def __init__(self):
        super().__init__()

        self.violations             = []
        self.sendViolation          = False
        self.receivingProb          = 0.5
        self.receivedModelCallBack  = None

    def run(self):
        while True:
            if len(self.violations) is not 0:
                del self.violations[0]
                print("Communicator: send violation")
                self.sendViolation = True
            elif self.sendViolation & (np.random.uniform(0,1,1)[0] > self.receivingProb):
                model = Model()
                print("Communicator: received new model")
                print("Communicator: send model to Learner")
                self.receivedModelCallBack(model)
                self.sendViolation = False


            time.sleep(3)

    def violation(self,model):
        self.violations.append(model)
        print("Communicator: received a violation")



class Learner(threading.Thread):

    def __init__(self):
        super().__init__()

        self.newModels          = []
        self.violationParam     = 0.95
        self.violationCallBack  = None
        self.data               = []
        self.waitingForNewModel = False
        self.model              = None

    def onNewData(self, data : np.array):
        self.data.append(data)
        print("Learner : received new data")

    def onNewModel(self, model):
        self.newModels.append(model)
        print("Learner: received new model")
        self.waitingForNewModel = False

    def getInitialModel(self):
        print("learner: request initial model")
        self.waitingForNewModel = True
        self.violationCallBack(None)

    def run(self):
        self.getInitialModel()

        while True:
            if self.waitingForNewModel:
                time.sleep(4)
            elif len(self.newModels) is not 0:
                self.model = self.newModels[0]
                print("learner: set new model")
                del self.newModels[0]
            elif len(self.data) is not 0:
                if self.model is None:
                    raise AttributeError
                del self.data[0]
                print("learner: optimized model parameters")
                if np.random.uniform(0,1,1)[0] > self.violationParam:
                    print("learner: obtained a violation")
                    self.waitingForNewModel = True
                    self.violationCallBack(self.model)

            time.sleep(1)

class DataSource(threading.Thread):

    def __init__(self):
        super().__init__()

        self.newDataCallBack    = None
        self.newDataProb        = 0.4

    def run(self):
        while True:
            if np.random.uniform(0,1,1)[0] > self.newDataProb:
                data = np.random.uniform(0,1,100)
                print("DataSource: send new data")
                self.newDataCallBack(data)
            time.sleep(1)


class Worker:

    def __init__(self):
        self.learner        = Learner()
        self.learner.setDaemon(True)

        self.dataSource     = DataSource()
        self.dataSource.setDaemon(True)

        self.communicator   = Commuincator()
        self.communicator.setDaemon(True)

        self.communicator.receivedModelCallBack = self.learner.onNewModel
        self.dataSource.newDataCallBack         = self.learner.onNewData
        self.learner.violationCallBack          = self.communicator.violation

    def run(self):
        self.dataSource.start()
        self.learner.start()
        self.communicator.start()

        while True:
            time.sleep(10)

if __name__ == "__main__":
    worker = Worker()
    worker.run()