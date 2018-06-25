from threading import Thread
import time

class Timeout(Thread):
    def register(self, timeoutFunc, timeout):
        self.timeoutFunc = timeoutFunc
        self.timeout = timeout
        return self
        
    def run(self):
        time.sleep(self.timeout)
        self.timeoutFunc()
        