from DLplatform.dataprovisioning import DataScheduler

import time

class IntervalDataScheduler(DataScheduler):
    def __init__(self, interval = 0.004, name = "IntervalDataScheduler"):
        DataScheduler.__init__(self, name = name)

        self._interval = interval

    def generateSample(self):
        '''

        Processes next data point from training dataset, i.e. appends it to the data buffer of the worker

        Returns
        -------

        '''

        while True:
            data = self.getData()
            time.sleep(self._interval)

            #if self._onDataUpdateCallBack is None:
            #    self.error("onUpdate call back function was not set")
            #    raise AttributeError("onUpdate call back function was not set")

            self.sendDataUpdate(data)
