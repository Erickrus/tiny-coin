# -*- coding: UTF-8
import hashlib as hasher

# Define what a TinyCoin block is
# 定义TinyCoin区块
class Block:
    # 初始化区块
    def __init__(self, index, timestamp, data, previousHash):
        self.index = index
        self.timestamp = timestamp
        self.data = data
        self.previousHash = previousHash
        self.hash = self.hash_block()
    
    # 计算hash值
    def hash_block(self):
        sha = hasher.sha256()
        sha.update((
            str(self.index) + 
            str(self.timestamp) + 
            str(self.data) + 
            str(self.previousHash)
        ).encode())
        return sha.hexdigest()