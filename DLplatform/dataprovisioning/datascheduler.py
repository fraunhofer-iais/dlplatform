from DLplatform.baseClass import baseClass
from DLplatform.dataprovisioning import DataSource

from abc import ABCMeta
from multiprocessing import Process
from pickle import dumps

class DataScheduler(baseClass, Process):
    '''
    Base class for scheduling data provision mechanism for learning Workers.
    Should be run in a separate Thread since it is an endless loop of 
    providing new examples.
    Associated with a DataSource that describes exact source of data to 
    provide to a Worker. Each Worker associated with its own unique DataScheduler.

    '''

    __metaclass__ = ABCMeta

    def __init__(self, name = "DataScheduler"):
        '''
        Initialize a parent class with name DataScheduler.
        Initialize a Process for method self.generateSamples.

        Returns
        -------
        None

        '''

        baseClass.__init__(self, name = name)
        Process.__init__(self, target = self.generateSamples)

        self._dataSource            = None

    def getData(self) -> tuple:
        '''
        Returns an example from the DataSource.
        Example is considered to be a tuple consisting of example and its label.

        Returns
        -------
        a training example together with label

        Exception
        --------
        AttributeError
            In case self._dataSource was not set

        '''

        if self._dataSource is None:
            self.error("Data source not set!")
            raise AttributeError("Data source not set!")
            
        return self._dataSource.getNext()

    def generateSamples(self):
        '''
        Main method that runs in an endless loop generating examples for training.
        Should be implemented in a particular DataScheduler.
        Calls method for the dataSource to be prepared, i.e., open the files for
        reading and cache them if it is pointed in options
        '''

        self._dataSource.prepare()

    def setConnection(self, workerConnection):
        '''
        Setter for the connection to worker in order
        to pass examples from the process of dataScheduler
        to the process of worker.

        Parameters
        ----------
        workerConnection : Connection
            the transmitter connection of a simplex pipe between the DataScheduler and the worker
        '''

        self._workerConnection = workerConnection

    def sendDataUpdate(self, data):
        '''

        Parameters
        ----------
        data
            the data to be send to the worker. It is most likely a tuple of numpy arrays
        Returns
        -------
        None

        Exception
        ---------
        '''

        if self._workerConnection is None:
            self.error("No workerConnection is set")
            raise AttributeError("No workerConnection is set")

        # preparing the msg send via pipe (should be smaller than 30 MiB according to Pipe documentation)
        msg = dumps(data)
        self._workerConnection.send(msg)

    def setDataSource(self, source : DataSource):
        '''
        Setter for DataSource, the object that has the data examples themselves

        Parameters
        ----------
        source : DataSource

        Returns
        -------
        None

        Exception
        ---------
        ValueError
            In case source is not of type DataSource
        '''

        if not isinstance(source,DataSource):
            error_text = "The attribute source is of type " + str(type(source)) + " and not of type" + str(DataSource)
            self.error(error_text)
            raise ValueError(error_text)

        self._dataSource = source

    def getDataSource(self) -> DataSource:
        '''
        Getter for DataSource

        Returns
        -------
        DataSource

        '''

        return self._dataSource

    def start(self):
        '''
        Starts process of the dataScheduler, that is an endless loop of providing data
        examples and pushing them to the pipe connected to the worker
        '''

        if (self._workerConnection == None):
            raise AttributeError("workerConnection wasn't set for the dataScheduler!")

        super().start()
