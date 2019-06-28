from DLplatform.baseClass import baseClass
from abc import ABCMeta
import inspect

class StoppingCriterion(baseClass):

    __metaclass__ = ABCMeta

    def __init__(self, name = "StoppingCriterion"):
        baseClass.__init__(self, name = name)

    def __call__(self, seenExamples: int, currentTimestamp: int) -> bool:

        raise NotImplementedError
    
    def getStrReprOfArg(self, arg) -> str:
        if isinstance(arg, str):
            return '\''+arg+'\''
        if hasattr(arg, '__dict__'): #only objects have the __dict__ attribute, but this is actually very ugly...
            #we assume boldly here that those classes have no parameters. 
            #Of course, to be correct, we would have to get their init parameters as well
            return arg.__class__.__name__ + "()"
        else:        
            return str(arg)
        
    def getInitParameters(self) -> str:
        argNames = inspect.getfullargspec(self.__init__).args
        initParameters = []
        for arg in argNames:
            if hasattr(self, arg):
                initParameters.append(arg + " = " + self.getStrReprOfArg(getattr(self, arg)))
        return ",".join(initParameters)
