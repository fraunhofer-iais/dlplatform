from DLplatform.stopping.stopping_criterion import StoppingCriterion

class Timeout(StoppingCriterion):
    def __init__(self, startTimestamp, duration, name = "Timeout"):
        StoppingCriterion.__init__(self, name = name)

        self.startTimestamp = startTimestamp
        self.duration = duration

    def __call__(self, seenExamples: int, currentTimestamp: int) -> bool:
        return currentTimestamp - startTimestamp >= self.duration
        
    def __str__(self):
        return "Timeout criterion (d=" + str(self.duration) + "ms)"
