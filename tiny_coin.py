# -*- coding: UTF-8
from flask import Flask
from flask import request
from flask import render_template

import json
import requests
import sys
import datetime as date
import copy
import time
import random
import socket

from block import Block
from timeout import Timeout
from logger import Logger
from tiny_coin_polling import TinyCoinPolling

node = Flask(__name__)


class TinyCoin:
    def __init__(self, mining=True, port=80):
        self.port = port
        # A completely random address of the owner of this node
        # 这是本节点所有者随机地址
        hostname = str(socket.gethostbyname(socket.gethostname()))
        
        self.minerAddress = "%s-%d" % (hostname, self.port)

        # This node's self.blockchain copy
        # 本节点的区块链拷贝
        self.blockchain = []
        self.blockchain.append(self.create_genesis_block())
        # Store the transactions that this node has in a list
        # 以列表的形式保存这个节点上的交易
        self.thisNodeTransactions = []
        # Store the url data of every other node in the network
        # so that we can communicate with them
        # 此处保存网络中所有其他节点的url, 这样就可以与其交互
        self.peerNodes = []
        # A variable to deciding if we're mining or not
        # 变量决定是否进行挖矿
        self.mining = mining
        

        Logger.info("TinyCoin.server: %s" % self.minerAddress)
        Logger.info("TinyCoin.mining: %s" % str(self.mining))
        
        #self.discover_peer_nodes()
        # 执行后台线程
        TinyCoinPolling().set(self).start()
    
    # Generate genesis block
    # 创建创世区块genesis block
    def create_genesis_block(self):
        # Manually construct a block with index zero and arbitrary previous hash
        # 手工构造创世区块, index=0, 同时强制构造上一个hash值
        return Block(0, date.datetime.now(), {
            "proof-of-work": 9,
            # 创世区块不包含任何交易
            "transactions": None
        }, "0")
    
    # 找到其他节点
    def _find_peer_nodes(self):
        Logger.info("TinyCoin._find_peer_nodes() - %s" % self.minerAddress)
        result = []
        for port in range(80, 90):
            try:
                # 此处跳过本机 同时查找其他地址
                if (port != self.port and 
                    requests.get("http://localhost:%d/ping" % port, timeout=0.1).content.decode() == "OK"):
                    result.append("http://localhost:%d" % port)
            except:
                pass
        self.peerNodes = result
    
    # 心跳函数
    def ping(self):
        return "OK"
        
    # 执行交易
    def transaction(self):
        Logger.info("TinyCoin.transaction() - %s" % self.minerAddress)
        # On each new POST request, we extract the transaction data
        # 每次POST请求发生时, 得到有交易数据
        newTransaction = request.get_json()
        
        # Then we add the transaction to our list
        # 然后将这个交易追加至本节点的交易列表
        self.thisNodeTransactions.append(newTransaction)
        # Because the transaction was successfully submitted, we log it to our console
        # 因为交易被成功提交, 打印出来, 在console中进行记录
        Logger.info("New transaction")
        Logger.info("FROM: {}".format(newTransaction['from'].encode('ascii','replace')))
        Logger.info("TO: {}".format(newTransaction['to'].encode('ascii','replace')))
        Logger.info("AMOUNT: {}\n".format(newTransaction['amount']))
        # Then we let the client know it worked out
        # 然后返回成功结果, 通知客户端提交成功
        return "Transaction submission successful\n"
    
    # 查询当前所有区块
    def get_blocks(self):
        Logger.info("TinyCoin.get_blocks() - %s" % self.minerAddress)
        # 不能简单实用 = 否则会出错
        chainToSend = copy.deepcopy(self.blockchain)
        # Convert our blocks into dictionaries, so we can send them as json objects later
        # 将区块链转换为字典, 便于后续通过json格式传输
        for i in range(len(chainToSend)):
            block = chainToSend[i]
            blockIndex = str(block.index)
            blockTimestamp = str(block.timestamp)
            blockData = str(block.data)
            blockHash = block.hash
            chainToSend[i] = {
                "index": blockIndex,
                "timestamp": blockTimestamp,
                "data": blockData,
                "hash": blockHash,
                "previousHash": block.previousHash,
            }
        chainToSend = json.dumps(chainToSend)
        return chainToSend
    
    # 寻找更新的链
    def _find_new_chains(self):
        # Get the blockchains of every other node
        # 获得本区块链上每个节点
        otherChains = []
        for nodeUrl in self.peerNodes:
            # Get their chains using a GET request
            # 通过GET请求, 获得其他节点上的链
            block = requests.get(nodeUrl + "/blocks").content
            # Convert the JSON object to a Python dictionary
            # 将返回的JSON对象转换成Python字典格式
            block = json.loads(block)
            # Add it to our list
            # 将其 加到otherChains, 后续在共识算法中处理
            otherChains.append(block)
        return otherChains
    
    # 反序列化区块链
    def _deserialize_blockchain(self):
        for i in range(len(self.blockchain)):
            block = self.blockchain[i]
            if type(block) == type({}):
                newBlock = Block(
                    int(block['index']),
                    block['timestamp'], 
                    eval(block['data']), 
                    block['previousHash']
                )
                self.blockchain[i] = newBlock
                
    # 共识算法
    def consensus(self):
        Logger.info("TinyCoin.consensus() - %s" % self.minerAddress)
        # Get the blocks from other nodes
        # 从其他节点获取区块
        otherChains = self._find_new_chains()
        # If our chain isn't longest, then we store the longest chain
        # 如果本地的区块链并不是最长的, 则保存最长的区块链
        longestChain = copy.deepcopy(self.blockchain)
        for chain in otherChains:
            if len(longestChain) < len(chain):
                longestChain = chain
        # If the longest chain isn't ours, then we stop mining and set our chain to the longest one
        # 如果最长的区块链不是本地, 终止挖矿操作, 把本地区块链设置成最长的一个
        self.blockchain = longestChain
        
        # 需要对收到的blockchain信息进行反序列化, 否则会出错
        self._deserialize_blockchain()

        return "OK"
    
    # 作为proof_of_work的一个服务函数 被外部调用
    def pow_service(self):
        Logger.info("TinyCoin.pow_service() - %s" % self.minerAddress)
        proofRequest = request.get_json()
        proofFrom = proofRequest['proof-from'].encode('ascii','replace').decode()
        lastProof = int(proofRequest['last-proof'])
        
        result = {
            "proof-from": proofFrom,
            "proof-by": self.minerAddress,
            'last-proof': lastProof,
            'proof-of-work': self.proof_of_work(lastProof)
        }
        
        return json.dumps(result)
    
    # 工作量证明 PoW
    def proof_of_work(self, lastProof):
        Logger.info("TinyCoin.proof_of_work() - %s" % self.minerAddress)
        # Create a variable that we will use to find our next proof of work
        # 建立变量, 用来找到下一个PoW
        incrementor = lastProof + 1
        # Keep incrementing the incrementor until it's equal to a number divisible by 9
        # and the proof of work of the previous block in the chain
        # 不断增加累加器(incrementor), 直到其数可以被9整除(incrementor % 9 == 0)
        # 同时PoW, 累加器数值可被链中上一个PoW整除。由于上一个PoW会越来越大, 导致工作量到后续也会不断增加
        while not (
            incrementor % 9 == 0 and 
            incrementor % lastProof == 0):
            # 让工作量计算 更耗时一些
            time.sleep(float(random.randint(0, 10)) / 10000.0)
            incrementor += 1
            
        # Once that number is found, we can return it as a proof of our work
        # 一旦找到了这个数字, 就返回工作量证明
        return incrementor
    
    
    # @node.route('/mine', methods = ['GET'])
    def mine(self):
        Logger.info("TinyCoin.mine() - %s" % self.minerAddress)
        if not self.mining:
            # 应该要实现一个broadcast.with(transaction) 的操作
            # 让其他某个服务器 代理工作 计算出PoW数值
            return "DO NOT MINING"
        # Get the last proof of work
        # 获得最后工作量证明PoW
        lastBlock = self.blockchain[-1]
        if type(lastBlock) == type({}):
            lastProof = eval(lastBlock['data'])['proof-of-work']
        else:
            lastProof = lastBlock.data['proof-of-work']
            
        # Find the proof of work for the current block being mined
        # Note: The program will hang here until a new  proof of work is found
        # 为当前正在挖矿的块, 找到工作量证明
        proof = self.proof_of_work(lastProof)

        return self._keep_account(lastBlock, proof, self.minerAddress)
        
    # 记账
    def _keep_account(self, lastBlock, proof, rewardTo):
        Logger.info("TinyCoin._keep_account(%d, %s) - %s" % (proof, rewardTo, self.minerAddress))
        
        # Once we find a valid proof of work,
        # we know we can mine a block so we reward the miner by adding a transaction
        # 一旦找到了一个有效的PoW, 矿工便可以得到奖励 - 通过增加一次交易
        self.thisNodeTransactions.append(
            { "from": "network", "to": rewardTo, "amount": 1 }
        )
        # Now we can gather the data needed to create the new block
        # 现在, 收集建立新区块的数据
        newBlockData = {
            "proof-of-work": proof,
            # 新的区块包含额外的transaction
            # 这里区块的信息中包含之前收到的交易, 以及奖励所得到的交易
            "transactions": list(self.thisNodeTransactions)
        }
        newBlockIndex = lastBlock.index + 1
        newBlockTimestamp = date.datetime.now()
        lastBlockHash = lastBlock.hash
        # Empty transaction list
        # 清空交易列表
        self.thisNodeTransactions[:] = []
        # Now create the new block!
        # 此处创建新的区块
        minedBlock = Block(
            newBlockIndex,
            newBlockTimestamp,
            newBlockData,
            lastBlockHash
        )
        self.blockchain.append(minedBlock)
        # Let the client know we mined a block
        # 通知客户端, 挖到了一个新的区块 (返回结果)
        return json.dumps({
                "index": newBlockIndex,
                "timestamp": str(newBlockTimestamp),
                "data": newBlockData,
                "hash": lastBlockHash
        }) + "\n"
    
    def _request_for_consensus(self):
        Logger.info("TinyCoin._request_for_consensus() - %s" % self.minerAddress)
        self.consensus()
        for nodeUrl in self.peerNodes:
            requests.get(nodeUrl + "/consensus")
        
    def _request_for_mine(self):
        Logger.info("TinyCoin._request_for_mine() - %s" % self.minerAddress)
        if self.mining:
            self.mine()
        else:
            maxMiningRequestNum = 2
            mineNodes = copy.deepcopy(self.peerNodes)
            random.shuffle(mineNodes)
            mineNodes = mineNodes[:
                min(
                    len(mineNodes), 
                    maxMiningRequestNum
                )
            ]
            
            # 获得最后一个区块
            lastBlock = self.blockchain[-1]
            if type(lastBlock) == type({}):
                lastProof = eval(lastBlock['data'])['proof-of-work']
            else: 
                lastProof = lastBlock.data['proof-of-work']
            
            # 通过异步调用 执行
            asyncPow = []
            for i in range(len(mineNodes)):
                mineNode = mineNodes[i]
                powRequest = {'proof-from': self.minerAddress, 'last-proof':lastProof}
                def local_post():
                    return requests.post(mineNode + "/pow", json = powRequest)
                asyncPow.append(Timeout())
                asyncPow[i].set(local_post, 0)
                asyncPow[i].start()
            
            powRes = None
            foundPow = False
            while not foundPow:
                for i in range(len(asyncPow)):
                    if asyncPow[i].result != None:
                        foundPow = True
                        print(asyncPow[i].result.content.decode())
                        powRes = json.loads(asyncPow[i].result.content.decode())
                        break
                time.sleep(0.005)
            
            self._keep_account(lastBlock, powRes['proof-of-work'], powRes['proof-by'])
    
    # 注册所有的在线服务函数
    def register_service(self, app):
        Logger.info("TinyCoin.register_service() - %s" % self.minerAddress)
        
        # mining and transaction use POST
        app.add_url_rule("/pow", "pow", self.pow_service, methods=['POST'])
        app.add_url_rule("/txion", "txion", self.transaction, methods=['POST'])
        
        app.add_url_rule("/blocks", "blocks", self.get_blocks, methods=['GET'])
        app.add_url_rule("/ping", "ping", self.ping, methods=['GET'])
        app.add_url_rule("/consensus", "consensus", self.consensus, methods=['GET'])
        
        # do not expose mine()
        #app.add_url_rule("/mine", "mine", self.mine, methods=['GET'])

minerAddress = ""

def main():
    node.add_url_rule("/index.html", "index.html", homepage, methods=['GET'])
    
    mining, port = True, 80
    if len(sys.argv) > 1:
        port = int(sys.argv[1])

    if len(sys.argv) > 2:
        if sys.argv[2].lower() == "false":
            mining = False

    tc = TinyCoin(mining = mining, port = port)
    tc.register_service(node)
    
    global minerAddress
    minerAddress = tc.minerAddress
    
    node.run(host='0.0.0.0', port=port)

def homepage():
    Logger.info("homepage() - %s" % minerAddress)
    return render_template("index.html", minerAddress=minerAddress)

if __name__ == "__main__":
    main()
