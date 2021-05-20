import carla
from enum import Enum

class Strategy(Enum):
    CONSTANT = 0
    INTERMITTENT = 1
    TRANSIENT = 2
    CRASH = 3

class FaultySensor(carla.Sensor):
    strategy = Strategy.CONSTANT
    target = 0
    counter = 0
    
    def __masterCallback(self, image, callback, faultCallback):
        faultyImage = faultCallback(image)
        callback(faultyImage)
        
    def __intermittentCallback(self, image, callback, faultCallback):
        self.counter = self.counter + 1
        if(self.counter >= self.target):
            self.counter = 0
            self.__masterCallback(image, callback, faultCallback) #called after interval
        else:
            callback(image)
     
    def __transientCallback(self, image, callback, faultCallback):
        if(self.counter >= self.target):
            self.__masterCallback(image, callback, faultCallback) #called constantly after time
        else:
            self.counter = self.counter + 1
            callback(image)

    def __crashCallback(self, image, callback, faultCallback):
        if(self.counter == self.target):
            self.counter = self.counter + 1
            self.__masterCallback(image, callback, faultCallback) #called once
        elif(self.counter < self.target):
            self.counter = self.counter + 1
            callback(image)
    
    def listen(self, callback, faultCallback):
        if(self.strategy == Strategy.CONSTANT):
            super().listen(lambda image: FaultySensor.__masterCallback(self, image, callback, faultCallback))
        elif(self.strategy == Strategy.INTERMITTENT):
            super().listen(lambda image: FaultySensor.__intermittentCallback(self, image, callback, faultCallback))
        elif(self.strategy == Strategy.TRANSIENT):
            super().listen(lambda image: FaultySensor.__transientCallback(self, image, callback, faultCallback))
        elif(self.strategy == Strategy.CRASH):
            super().listen(lambda image: FaultySensor.__crashCallback(self, image, callback, faultCallback))

def ToFaultySensor(sensor):
    sensor.__class__ = FaultySensor
    return sensor
