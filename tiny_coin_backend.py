from threading import Thread
import time

class TinyCoinBackend(Thread):
    
    def set(self, tinyCoin):
        self.tinyCoin = tinyCoin
    
    def run(self):
        loopCounter = 0
        while True:
            # task 1 discover peer node
            if loopCounter % 100 == 10:
                self.tinyCoin._find_peer_nodes()
            
            # task 2 mine and consensus
            if loopCounter % 10 == 1:
                if len(self.tinyCoin.thisNodeTransactions) > 0:
                    self.tinyCoin._request_for_mine()
                    self.tinyCoin._request_for_consensus()
            
            loopCounter += 1
            time.sleep(0.5)

        