from DLplatform.dataprovisioning import DataScheduler

import time

class BatchDataScheduler(DataScheduler):
    def __init__(self, name = "BatchDataScheduler"):
        DataScheduler.__init__(self, name = name)

    def generateSamples(self):
        '''

        Processes next data point from training dataset, i.e. appends it to the data buffer of the worker

        Returns
        -------

        '''
        DataScheduler.generateSamples(self)

        while True:
            data = self.getData()
            self.sendDataUpdate(data)
