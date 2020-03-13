from DLplatform.aggregating import Aggregator

from DLplatform.parameters import Parameters
from typing import List
import numpy as np
from scipy.spatial.distance import cdist, euclidean

class GeometricMedian(Aggregator):
    '''
    Provides a method to calculate an averaged model from n individual models (using the arithmetic mean)
    '''

    def __init__(self, name="Geometric median"):
        '''

        Returns
        -------
        None
        '''
        Aggregator.__init__(self, name=name)

    def calculateDivergence(self, param1, param2):
        return np.linalg.norm(param1 - param2)

    def __call__(self, params: List[Parameters]) -> Parameters:
        '''

        This aggregator takes n lists of model parameters and returns a list of component-wise arithmetic means.

        Parameters
        ----------
        params A list of Paramters objects. These objects support addition and scalar multiplication.

        Returns
        -------
        A new parameter object that is the average of params.

        '''
        Z = []
        for param in params:
            Z_i = param.toVector()
            Z.append(Z_i)
        Z = np.array(Z) #TODO: check that the shape is correct (that is, that no transpose is required)
        gm = self.calcGeometricMedian(Z) #computes the GM for a numpy array
        newParam = params[0].getCopy()#by copying the parameters object, we ensure that the shape information is preserved
        newParam.fromVector(gm) 
        return newParam
    
    def calcGeometricMedian(self, X, eps=1e-5, mat_iter = 10e6):
        y = np.mean(X, 0)
        iterCount = 0
        
        while iterCount <= mat_iter:
            D = cdist(X, [y])
            nonzeros = (D != 0)[:, 0]
    
            Dinv = 1 / D[nonzeros]
            Dinvs = np.sum(Dinv)
            W = Dinv / Dinvs
            T = np.sum(W * X[nonzeros], 0)
    
            num_zeros = len(X) - np.sum(nonzeros)
            if num_zeros == 0:
                y1 = T
            elif num_zeros == len(X):
                return y
            else:
                R = (T - y) * Dinvs
                r = np.linalg.norm(R)
                rinv = 0 if r == 0 else num_zeros/r
                y1 = max(0, 1-rinv)*T + min(1, rinv)*y
    
            if euclidean(y, y1) < eps:
                return y1
    
            y = y1
            iterCount += 1

    def __str__(self):
        return "Geometric median"
    
               
#     def setToGeometricMedian(self, params : List):
#         models = params
# 
#         shapes = []
#         b = []
#         once = True
#         newWeightsList = []
#         try:
#             for i, model in enumerate(models):
#                 w2 = model.get()
#                 c = []
#                 c = np.array(c)
#                 for i in range(len(w2)):
#                     z = np.array(w2[i])
# 
#                     if len(shapes) < 8:
#                         shapes.append(z.shape)
#                     d = np.array(w2[i].flatten()).squeeze()
#                     c = np.concatenate([c, d])
#                 if (once):
#                     b = np.zeros_like(c)
#                     b[:] = c[:]
#                     once = False
#                 else:
#                     once = False
#             b = np.concatenate([b.reshape((-1, 1)), c.reshape((-1, 1))], axis=1)
#             median_val = np.array(b[0]) #hd.geomedian(b))
#             sizes = []
#             for j in shapes:
#                 size = 1
#                 for k in j:
#                     size *= k
#                 sizes.append(size)
#             newWeightsList = []
# 
#             chunks = []
#             count = 0
#             for size in sizes:
#                 chunks.append([median_val[i + count] for i in range(size)])
#                 count += size
#             for chunk, i in zip(chunks, range(len(shapes))):
#                 newWeightsList.append(np.array(chunk).reshape(shapes[i]))
# 
#         except Exception as e:
#             print("Error happened! Message is ", e)
#         self.set(newWeightsList)
    

