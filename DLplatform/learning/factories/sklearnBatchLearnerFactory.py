from DLplatform.learning.learner import BatchLearner, Learner

class SklearnBatchLearnerFactory():
    def __init__(self, sklearnLearner : BatchLearner, sklearnParams : dict):
        self.sklearnLearner = sklearnLearner
        self.sklearnParams = sklearnParams
    
    def getLearner(self) -> Learner:
        return self.sklearnLearner(**self.sklearnParams)
    
    def getLearnerOnDevice(self, mode, device):
        return self.sklearnLearner(**self.sklearnParams)
    
    def __str__(self):
        return "Scikit-learn batch learner factory."
