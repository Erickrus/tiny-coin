# -*- coding: UTF-8
from threading import Thread
import time

class TinyCoinPolling(Thread):
    
    def set(self, tinyCoin):
        self.tinyCoin = tinyCoin
        return self
    
    def run(self):
        loopCounter = 0
        while True:
            # task 1 发现并更新节点
            if loopCounter % 500 == 10:
                self.tinyCoin._find_peer_nodes()
            
            # task 2 完成当前交易并寻求共识
            if loopCounter % 10 == 1:
                if len(self.tinyCoin.thisNodeTransactions) > 0:
                    self.tinyCoin._request_for_mine()
                    self.tinyCoin._request_for_consensus()
            
            loopCounter += 1
            time.sleep(0.5)

        