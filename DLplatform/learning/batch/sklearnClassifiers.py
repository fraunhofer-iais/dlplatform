
import numpy as np
from typing import List
from DLplatform.learning.learner import BatchLearner
from DLplatform.parameters.vectorParameters import VectorParameter
from sklearn.linear_model import LogisticRegression as LR

class LogisticRegression(BatchLearner):
    def __init__(self, regParam, dim, solver = 'lbfgs', name = "LogisticRegression"):
        BatchLearner.__init__(self, name = name)
        self.regParam = regParam
        self.dim = dim
        self.solver = solver
        self.model = LR(C=self.regParam, solver=self.solver)
        self.model.coef_ = np.zeros(dim-1)
        self.model.intercept_ = np.array([0.0])
        #self.weights = np.zeros(dim)
        
    def setModel(self, param: VectorParameter, setReference: bool):
        super(LogisticRegression, self).setModel(param, setReference)
        
        #self.info('STARTTIME_setReference: '+str(time.time()))
        if setReference:
            self._flattenReferenceParams = param.get()
        #self.info('ENDTIME_setReference: '+str(time.time()))


    def train(self, data: List) -> List:
        '''
        Training

        Parameters
        ----------
        data - training batch

        Returns
        -------
        list - first element is loss suffered on this training
                second element are predictions on the training data

        '''

        if not isinstance(data, List):
            error_text = "The argument data is not of type" + str(List) + "it is of type " + str(type(data))
            self.error(error_text)
            raise ValueError(error_text)
        X = np.asarray([record[0] for record in data])
        y = np.asarray([record[1] for record in data])
        score = self.model.fit(X, y).score(X,y)
        preds = self.model.predict(X)
        
        return score, preds

    def setParameters(self, param : VectorParameter):
        '''

        Replace the current values of the model parameters with the values of "param"

        Parameters
        ----------
        param

        Returns
        -------

        Exception
        ---------
        ValueError
            in case that param is not of type Parameters
        '''

        if not isinstance(param, VectorParameter):
            error_text = "The argument param is not of type" + str(VectorParameter) + "it is of type " + str(type(param))
            self.error(error_text)
            raise ValueError(error_text)
        #TODO: so far, we assume that the intercept is a scalar, but it can be also a 1d-array with len > 1. This would have to be configured somehow...
        w = param.get().tolist()
        b = w[-1]
        del w[-1]
        self.model.coef_ = np.array(w)
        self.model.intercept_ = np.array([b])

        

    def getParameters(self) -> VectorParameter:
        '''

        Takes the current model parameters and hands them to a KerasNNParameters object which is returned

        Returns
        -------
        Parameters

        '''
        wb = np.concatenate((self.model.coef_.flatten(), self.model.intercept_))
        if isinstance(self.model.intercept_, List): #in principle, the intercept can be a lit. But this may break at other points, then.
            wb = np.array(self.model.coef_[0].tolist() + self.model.intercept_.tolist())
        return VectorParameter(wb)

    def calculateCurrentDivergence(self):
        return np.linalg.norm(self.getParameters().get() - self._flattenReferenceParams)