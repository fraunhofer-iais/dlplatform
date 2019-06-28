from DLplatform.parameters import Parameters

import numpy as np
from typing import List
    
class KerasNNParameters(Parameters):
    '''
    Specific implementation of Parameters class for KerasNN learner
    Here we know that parameters are list of numpy arrays. All the methods 
    for addition, multiplication by scalar, flattening and finding distance
    are contained in this class.

    '''

    def __init__(self, weights : list):
        '''
        Initialize with setting the weights values

        Parameters
        ----------
        weights - List of weights values extracted from the network with Keras method get_weights

        Returns
        -------
        None

        '''
        self.weights = weights

    def set(self, weights: list):
        '''
        Set the weights values
        If needed to update weights inside of an existing parameters object

        Parameters
        ----------
        weights - List of weights values extracted from the network with Keras method get_weights

        Returns
        -------
        None

        Exception
        ---------
        ValueError
            when weights are not a list or elements of the weights list are not numpy arrays

        '''
        if not isinstance(weights, list):
            raise ValueError("Weights for KerasNNParameters should be given as list of numpy arrays. Instead, the type given is " + str(type(weights)))
            for arr in weights:
                if not isinstance(arr, np.ndarray):
                    raise ValueError("Weights for KerasNNParameters should be given as list of numpy arrays. Instead, one element of list is of type " + str(type(arr)))
        
        self.weights = weights
        # to use it inline
        return self

    def get(self) -> list:
        '''
        Get the weights values

        Returns
        -------
        list of numpy arrays with weights values

        '''
        return self.weights
    
    def add(self, other):
        '''
        Add other parameters to the current ones
        Expects that it is the same structure of the network

        Parameters
        ----------
        other - Parameters of the other network

        Returns
        -------
        None

        Exception
        ---------
        ValueError
            in case if other is not an instance of KerasNNParameters
            in case when the length of the list of weights is different
        Failure
            in case if any of numpy arrays in the weights list have different length

        '''
        if not isinstance(other, KerasNNParameters):
            error_text = "The argument other is not of type" + str(KerasNNParameters) + "it is of type " + str(type(other))
            self.error(error_text)
            raise ValueError(error_text)

        otherW = other.get()
        if len(self.weights) != len(otherW):
            raise ValueError("Error in addition: list of weights have different length. This: "+str(len(self.weights))+", other: "+str(len(otherW))+".")
        
        for i in range(len(otherW)):
            self.weights[i] = np.add(self.weights[i], otherW[i])
    
    def scalarMultiply(self, scalar: float):
        '''
        Multiply weight values by the scalar

        Returns
        -------
        None

        Exception
        ---------
        ValueError
            in case when parameter scalar is not float

        '''
        if not isinstance(scalar, float):
            raise ValueError("Scalar should be float but is " + str(type(scalar)) + ".")
        
        for i in range(len(self.weights)):
            self.weights[i] *= scalar
            
    
    def distance(self, other) -> float:
        '''
        Calculate euclidian distance between two parameters set
        Flattens all the weights and gets simple norm of difference

        Returns
        -------
        distance between set of weights of the object and other parameters

        Exception
        ---------
        ValueError
            in case the other is not KerasNNParameters
            in case when length of the list of weights is different
        Failure
            in case when flattened vecrtors are different by length

        '''
        if not isinstance(other, KerasNNParameters):
            error_text = "The argument other is not of type" + str(KerasNNParameters) + "it is of type " + str(type(other))
            self.error(error_text)
            raise ValueError(error_text)

        otherW = other.get()
        if len(self.weights) != len(otherW):
            raise ValueError("Error in addition: list of weights have different length. This: "+str(len(self.weights))+", other: "+str(len(otherW))+".")
        
        w1 = self.flatten()
        w2 = other.flatten() #instead of otherW, because otherW is of type np.array instead of paramaters
        dist = np.linalg.norm(w1-w2)
        
        return dist
    
    def flatten(self) -> np.ndarray:
        '''
        Get the flattened version of weights

        Returns
        -------
        numpy array of all the layers weights flattenned and concatenated

        '''
        flat_w = []
        for wi in self.weights:
            flat_w += np.ravel(wi).tolist()
        return np.asarray(flat_w)
    
    def getCopy(self):
        '''
        Creating a copy of paramaters with the same weight values as in the current object

        Returns
        -------
        KerasNNParameters object with weights values from the current object

        '''
        newWeights = []
        for arr in self.weights:
            newWeights.append(arr.copy())
        newParams = KerasNNParameters(newWeights)
        return newParams