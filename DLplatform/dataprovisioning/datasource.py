from DLplatform.baseClass import baseClass

from abc import ABCMeta

class DataSource(baseClass):

    '''
    Super class of the different dataset-dependent data source classes.
    '''

    __metaclass__ = ABCMeta

    def __init__(self, name = "DataSource"):
        '''

        Returns
        -------
        None
        '''
        baseClass.__init__(self, name = name)

    def getNext(self):
        '''

        This method is implemented in sub-classes of 'DataSource'.

        Parameters
        ----------

        Returns
        -------
        tuple
        '''
        raise NotImplementedError
