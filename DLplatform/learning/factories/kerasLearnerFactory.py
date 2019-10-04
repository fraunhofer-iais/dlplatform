from DLplatform.learning.factories import LearnerFactory


class KerasNetwork():
    def __init__(self):
        pass
    
    def __call__(self):
        return None

    def __str__(self):
        return "KerasNetwork"

class KerasLearnerFactory(LearnerFactory):

    '''

    Provides a factory method that sets up a neural network whose architecture depends on the input parameters 'dataset' and 'modeltype'.

    This neural networks is assigned to a learner object which is returned.

    '''
    def __init__(self, network : KerasNetwork, updateRule, learningRate, lossFunction, batchSize, syncPeriod, delta):
        self.network        = network
        self.updateRule     = updateRule
        self.learningRate   = learningRate
        self.lossFunction   = lossFunction
        self.batchSize      = batchSize
        self.syncPeriod     = syncPeriod
        self.delta          = delta
        
    def getLearner(self):
        from DLplatform.learning.deeplearning.kerasNN import KerasNN
        import tensorflow as tf
        from keras import optimizers

        graph = tf.Graph()
        with graph.as_default():
            nn = self.network()
            optimizer = eval("optimizers." + self.updateRule + "(lr=" + str(self.learningRate) + ")")
            nn.compile(loss=self.lossFunction, optimizer=optimizer)
            nn.metrics_tensors += nn.outputs
                
            config = tf.ConfigProto()
            config.gpu_options.allow_growth = True
            session = tf.Session(graph = graph, config = config)
            session.run(tf.global_variables_initializer())

        learner = KerasNN(batchSize=self.batchSize, syncPeriod=self.syncPeriod, delta=self.delta, session=session)
        learner.setCore(nn)
        return learner

    def getLearnerOnDevice(self, mode, device):
        return self.getLearner()

    def __str__(self):
        return "Keras Learner, network " + str(self.network) + ", update rule " + self.updateRule +", learning rate " + str(self.learningRate) + ", loss function " + self.lossFunction + ", batch size " + str(self.batchSize) + ", sync period " + str(self.syncPeriod) + ", delta " + str(self.delta)
