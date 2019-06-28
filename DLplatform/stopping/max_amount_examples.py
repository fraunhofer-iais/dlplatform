from DLplatform.stopping.stopping_criterion import StoppingCriterion

class MaxAmountExamples(StoppingCriterion):
    def __init__(self, maxAmount, name = "MaxAmountExamples"):
        StoppingCriterion.__init__(self, name = name)

        self.maxAmount = maxAmount

    def __call__(self, seenExamples: int, currentTimestamp: int) -> bool:
        return seenExamples >= self.maxAmount
        
    def __str__(self):
        return "Max amount examples criterion (n=" + str(self.maxAmount) + ")"
