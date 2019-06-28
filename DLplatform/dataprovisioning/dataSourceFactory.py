from DLplatform.dataprovisioning.datasource import DataSource
import inspect
import types

class DataSourceFactory():
    def __init__(self):
        pass
    
    def getDataSource(self, nodeId) -> DataSource:
        pass
    
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