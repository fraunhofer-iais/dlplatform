import numpy as np
from DLplatform.parameters.parameters import Parameters

class VectorParameter(Parameters):
    '''
    Parameters that are represented as a 1d numpy array.
    '''

    def __init__(self, weights : np.ndarray):
        self._weights = weights.flatten()
        self.dim = self._weights.shape[0]

    def set(self, weights : np.ndarray):
        if not isinstance(weights, np.ndarray):
            raise ValueError("Weights for ParametersVector should be given as numpy array. Instead, the type given is " + str(type(weights)))
        if weights.shape[0] != self.dim:
            raise ValueError("Dimension of parameters was ", self.dim," at initialization, it is now set to ",weights.shape[0],".")
        self._weights = weights.flatten()

    def get(self) -> np.ndarray:
        return self._weights
    
    def add(self, other):
        if not isinstance(other, VectorParameter):
            raise ValueError("Other parameters needs to be VectorParameters as well, instead it is " + str(type(other)))
        otherW = other.get()
        if not isinstance(otherW, np.ndarray):
            raise ValueError("Weights for ParametersVector should be given as numpy array. Instead, the type given is " + str(type(other)))
        if otherW.shape != self._weights.shape:
            raise ValueError("Dimension of parameters for addition (",other.shape[0],") does not match this ones: ", self.dim,".")
        self._weights = np.add(self._weights, otherW)
    
    def scalarMultiply(self, scalar : float):
        self._weights *= scalar
    
    def distance(self, other) -> float:
        if not isinstance(other, VectorParameter):
            raise ValueError("Other parameters needs to be VectorParameters as well, instead it is " + str(type(other)))
        #calculates the Euclidean distance 
        other = other.get()
        if not isinstance(other, np.ndarray):
            raise ValueError("Weights for ParametersVector should be given as numpy array. Instead, the type given is " + str(type(other)))
        other = other.flatten()
        if other.shape != self._weights.shape:
            raise ValueError("Dimension of parameters for addition (",other.shape[0],") does not match this ones: ", self.dim,".")
         
        return np.linalg.norm(self._weights - other)
    
    def getCopy(self) -> np.ndarray:
        return VectorParameter(self._weights.copy())