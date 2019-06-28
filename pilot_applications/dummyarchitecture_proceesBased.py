'''
created on 16.08.2018

author twirtz
'''

from multiprocessing import Process, Pipe
import numpy as np
from pickle import dumps, loads
import time

class Model:

    def __init__(self, id = ""):
        self.id = id



class Commuincator(Process):


    def __init__(self,
                 workerPipe     = None,
                 learnerPipe    = None):
        super().__init__()

        self.violations             = []
        self.sendViolation          = False
        self.receivingProb          = 0.5
        self.requestProbability     = 0.98
        self.workerPipe             = workerPipe
        self.learnerPipe            = learnerPipe
        self.modelCounter           = 1
    def run(self):
        while True:
            if self.sendViolation & (np.random.uniform(0, 1, 1)[0] > self.receivingProb):
                model = Model("model_" + str(self.modelCounter))
                self.sendModelToLearner(model)
                self.modelCounter = self.modelCounter+ 1
            elif (not self.sendViolation) & (np.random.uniform(0, 1, 1)[0] > self.requestProbability):
                self.sendRequestToWorker()

            self.checkCommunication()
            time.sleep(1)

    def checkCommunication(self):
        if self.learnerPipe.poll():

            recvObj     = self.learnerPipe.recv()

            if not isinstance(recvObj,tuple):
                raise ValueError("recvObj is not a tuple")
            elif not len(recvObj) == 2:
                raise ValueError("the length of recvObj is different from 2")

            key, value  = recvObj
            if value != None:
                value       = loads(value)

            print("communicator received " + key)

            if key == "VIOLATION":
                self.sendViolation = True
                if not isinstance(value,Model):
                    raise ValueError("recvObj[1] is not of type Model it is of type " + value.__class__.__name__ )
                print("Send violation to Coordinator")
            elif key == "SENDMODEL":
                if not isinstance(value,Model):
                    raise ValueError("recvObj[1] is not of type Model it is of type " + value.__class__.__name__ )
                print("Send model to Coordinator")
            elif key == "INITIALMODEL":
                self.sendViolation = True
            print("communicator request initial model form coordinator")

    def sendModelToLearner(self,model):
        sendObj = ("NEWMODEL",dumps(model))
        self.workerPipe.send(sendObj)
        self.sendViolation = False
        print("communicator send new model to worker")

    def sendRequestToWorker(self):
        sendObj = ("MODELREQUEST", None)
        self.workerPipe.send(sendObj)
        print("communicator send model request to worker")


class Learner():

    def __init__(self,
                 communicatorPipe):
        self.waitingForNewModel = False
        self.communicatorPipe   = communicatorPipe

        self.batchSize          = 1
        self.data               = []
        self.model              = None
        self.violationParam     = 0.8
        self.getInitialModel()


    def getInitialModel(self):
        print("learner: request initial model")
        self.waitingForNewModel = True
        self.requestInitialModel()

    def canObtainData(self):
        return not self.waitingForNewModel

    def obtainData(self,data):

        self.data.append(data)
        print("learner: obtained data")
        if self.waitingForNewModel:
            time.sleep(4)
        elif len(self.data) >= self.batchSize:
            del self.data[:self.batchSize]
            print("learner: optimized model parameters")
            if np.random.uniform(0, 1, 1)[0] > self.violationParam:
                print("learner: obtained a violation")
                self.waitingForNewModel = True
                self.sendViolation()

            time.sleep(1)

    def sendViolation(self):
        msg = dumps(self.model)
        self.communicatorPipe.send(("VIOLATION", msg))
        print("learner sends violation to communicator")

    def sendParameters(self):
        msg = dumps(self.model)
        self.communicatorPipe.send(("MODELREQUEST", msg))
        print("learner sends parameters to communicator")

    def requestInitialModel(self):
        self.communicatorPipe.send(("INITIALMODEL",None))
        print("learner request for initial model")

    def setModel(self,model):
        self.waitingForNewModel = False
        self.model              = model
        print("learner sets new model")

class DataSource(Process):

    def __init__(self,
                 workerPipe = None):

        super().__init__()

        self.workerPipe         = workerPipe
        self.newDataProb        = 0.4

    def run(self):
        while True:
            if np.random.uniform(0,1,1)[0] > self.newDataProb:
                data = np.random.uniform(0,1,100)
                self.sendData(data)
            time.sleep(1)

    def sendData(self,data):
        self.workerPipe.send(("DATA",data))
        print("data source send data to worker")


class Worker:

    def __init__(self):
        # initiallizing pipes for communication
        commPipe                = Pipe(duplex=False)
        dataPipe                = Pipe(duplex=False)
        learnerPipe             = Pipe(duplex=False)

        # here is worker receiver only
        self.communicatorPipe   = commPipe[0]
        self.dataSourcePipe     = dataPipe[0]

        # communicator is receiver for the learner and transmitter for worker pipe
        self.communicator       = Commuincator(workerPipe       = commPipe[1],
                                               learnerPipe      = learnerPipe[0])
        self.dataSource         = DataSource  (workerPipe       = dataPipe[1])

        self.learner            = Learner     (communicatorPipe = learnerPipe[1])

        self.data               = []
        self.batchSize          = 5

    def checkCommunication(self):
        if self.communicatorPipe.poll():

            recvObj     = self.communicatorPipe.recv()

            if not isinstance(recvObj,tuple):
                raise ValueError("recvObj is not a tuple")
            elif not len(recvObj) == 2:
                raise ValueError("the length of recvObj is different from 2")

            key, value  = recvObj

            print("worker received " + key + " from communicator")
            if key == "MODELREQUEST":
                print("worker forwarded model request to learner")
                self.learner.sendParameters()
            elif key == "NEWMODEL":
                value = loads(value)
                print("worker forwarded " + value.id + " to learner")
                if not isinstance(value,Model):
                    raise ValueError("recvObj[1] is not of type Model it is of type " + value.__class__.__name__ )
                self.learner.setModel(value)

        if self.dataSourcePipe.poll():

            recvObj     = self.dataSourcePipe.recv()

            if not isinstance(recvObj,tuple):
                raise ValueError("recvObj is not a tuple")
            elif not len(recvObj) == 2:
                raise ValueError("the length of recvObj is different from 2")

            key, value  = recvObj

            print("worker received " + key + " from dataSource")

            if key == "DATA":
                self.data.append(value)
                print("worker buffers data")

    def run(self):

        self.communicator.start()
        self.dataSource.start()

        while True:
            time.sleep(1)

            self.checkCommunication()

            if self.learner.canObtainData() & len(self.data) != 0:
                self.learner.obtainData(self.data[0])
                del(self.data[0])

        self.dataSource.join()
        self.communicator.join()


if __name__ == "__main__":
    worker = Worker()
    worker.run()