from DLplatform.exceptions import LoggerNotFoundError

from abc import ABCMeta
import logging

LOGGER_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'


class baseClass():
    '''
    Abstract class that provides fundamental naming ('getName','setName') and logging ('defineLogger','debug','error','info') functionalities.

    Most classes used in this communication framework inherit from 'baseClass'.
    '''

    # make it an abstract class
    __metaclass__   = ABCMeta
    #_logger         = None
    _name           = "baseClass"

    def __init__(self,
                 name ,
                 debug = False):
        '''

        Parameters
        ----------
        name: str - name of the object
        debug: boolean - determines logging level, is passed to 'defineLogger'

        Returns
        -------
        '''

        self.setName(name = name)

        # create logger
        self._logger = self.defineLogger(debug)
    
    '''
    When using multiprocessing, the baseclass is serialized using pickle (in windows, not so under linux). 
    However, the logge cannot be pickled, since it contains a thread.lock object.
    To avoid this, we implemented the following two functions which govern the behavior of pickle.
    In here, the logger object is disregarded, only its name is stored. With this name, the correct logger can be loaded, later.
    '''
    def __getstate__(self):
        d = self.__dict__.copy()
        if '_logger' in d:
            d['_logger'] = d['_logger'].name
        return d
    
    def __setstate__(self, d):
        if '_logger' in d:
            d['_logger'] = logging.getLogger(d['_logger'])
        self.__dict__.update(d)
        
    def defineLogger(self, debug):

        '''

        Configures and returns a logger.

        Parameters
        ----------
        debug: boolean - determines logging level

        Returns
        -------
        logger: object
        '''

        logger = logging.getLogger(self.getName())
        formatter = logging.Formatter(LOGGER_FORMAT)
        ch = logging.StreamHandler()
        ch.setFormatter(formatter)
        # add ch to logger
        logger.addHandler(ch)

        logger.setLevel(logging.WARNING)
        #if debug:
        #    logger.setLevel(logging.DEBUG)
        #else:
        #    logger.setLevel(logging.INFO)

        return logger


    def getName(self):
        '''

        Returns name of the object.

        Parameters
        ----------

        Returns
        -------
        name: str - name of the object
        '''

        return self._name

    def setName(self, name : str):
        '''

        Sets name of the object.

        Parameters
        ----------
        name

        Returns
        -------

        '''

        self._name = str(name)

    def debug(self, msg : str):
        '''

        Adds a message to the debug logging.

        Parameters
        ----------
        msg: str - message to be logged as debugging info

        Returns
        -------

        '''

        if self._logger is not None:
            self._logger.debug(msg)
        #else:
        #    raise LoggerNotFoundError


    def error(self, msg : str):
        '''

        Adds a message to the error logging.

        Parameters
        ----------
        msg: str - message to be logged as error info

        Returns
        -------

        '''

        if self._logger is not None:
            self._logger.error(msg)
        else:
            raise LoggerNotFoundError


    def info(self, msg : str):
        '''

        Adds a message to the info logging.

        Parameters
        ----------
        msg: str - message to be logged as info

        Returns
        -------

        '''

        if self._logger is not None:
            self._logger.info(msg)
        else:
            raise LoggerNotFoundError

