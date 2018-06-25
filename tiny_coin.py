# -*- coding: UTF-8
from flask import Flask
from flask import request
from flask import render_template

import json
import requests
import sys
import datetime as date
import copy

from block import Block
from timeout import Timeout

node = Flask(__name__)


class TinyCoin:
    def __init__(self, mining=True, port=80):
        self.port = port
        # A completely random address of the owner of this node
        # 这是本节点所有者随机地址
        self.minerAddress = "q3nf394hjg-%s-%d-34nf3i4nflkn3oi" % ("localhost", self.port)
        print(" * %s" % self.minerAddress)
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
        # A variable to deciding if we're self.mining or not
        # 变量决定是否进行挖矿
        self.mining = mining
        
        self.discover_peer_nodes()
        

    # 根据规则 发现节点
    def discover_peer_nodes(self):
        Timeout().set(self.find_peer_nodes, 5).start()
    
    # Generate genesis block
    # 创建创世块genesis block
    def create_genesis_block(self):
        # Manually construct a block with index zero and arbitrary previous hash
        # 手工构造一个区块, index=0, 同时强制构造上一个hash值
        return Block(0, date.datetime.now(), {
            "proof-of-work": 9,
            "transactions": None
        }, "0")
    
    # 找到其他节点
    def find_peer_nodes(self):
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
        
    def ping(self):
        return "OK"
        
    # @node.route('/txion', methods=['POST'])
    def transaction(self):
        # On each new POST request, we extract the transaction data
        # 每次POST请求发生时, 得到有交易数据
        newTransaction = request.get_json()
        
        # Then we add the transaction to our list
        # 然后将这个交易追加至本节点的交易列表
        self.thisNodeTransactions.append(newTransaction)
        # Because the transaction was successfully submitted, we log it to our console
        # 因为交易被成功提交, 打印出来, 在console中进行记录
        print("New transaction")
        print("FROM: {}".format(newTransaction['from'].encode('ascii','replace')))
        print("TO: {}".format(newTransaction['to'].encode('ascii','replace')))
        print("AMOUNT: {}\n".format(newTransaction['amount']))
        # Then we let the client know it worked out
        # 然后返回成功结果, 通知客户端提交成功
        return "Transaction submission successful\n"
    
    # @node.route('/blocks', methods=['GET'])
    def get_blocks(self):
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
    
    
    def find_new_chains(self):
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
    
    # 共识算法
    def consensus(self):
        # Get the blocks from other nodes
        # 从其他节点获取区块
        otherChains = self.find_new_chains()
        # If our chain isn't longest, then we store the longest chain
        # 如果本地的区块链并不是最长的, 则保存最长的区块链
        longestChain = self.blockchain
        for chain in otherChains:
            if len(longestChain) < len(chain):
                longestChain = chain
        # If the longest chain isn't ours, then we stop self.mining and set our chain to the longest one
        # 如果最长的区块链不是本地, 终止挖矿操作, 把本地区块链设置成最长的一个
        self.blockchain = longestChain
        
        # 需要对收到的blockchain信息进行反序列化
        # 否则会出错
        for i in range(len(self.blockchain)):
            block = self.blockchain[i]
            if type(block) == type({}):
                newBlock = Block(int(block['index']),block['timestamp'], eval(block['data']), block['previousHash'])
            self.blockchain[i] = newBlock
        
        return "OK"
    
    # 工作量证明 PoW
    def proof_of_work(self, lastProof):
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
            incrementor += 1
        # Once that number is found, we can return it as a proof of our work
        # 一旦找到了这个数字, 就返回工作量证明
        return incrementor
    
    # @node.route('/mine', methods = ['GET'])
    def mine(self):
        # Get the last proof of work
        # 获得最后工作量证明PoW
        lastBlock = self.blockchain[-1]
        if type(lastBlock) == type({}):
            print(lastBlock['data'])
            lastProof = eval(lastBlock['data'])['proof-of-work']
        else: 
            lastProof = lastBlock.data['proof-of-work']
            
        # Find the proof of work for the current block being mined
        # Note: The program will hang here until a new  proof of work is found
        # 为当前正在挖矿的块, 找到工作量证明
        proof = self.proof_of_work(lastProof)
        # Once we find a valid proof of work,
        # we know we can mine a block so we reward the miner by adding a transaction
        # 一旦找到了一个有效的PoW, 矿工便可以得到奖励 - 通过增加一次交易
        self.thisNodeTransactions.append(
            { "from": "network", "to": self.minerAddress, "amount": 1 }
        )
        # Now we can gather the data needed to create the new block
        # 现在, 收集建立新区块的数据
        newBlockData = {
            "proof-of-work": proof,
            "transactions": list(self.thisNodeTransactions)
        }
        newBlockIndex = lastBlock.index + 1
        newBlockTimestamp = thisTimestamp = date.datetime.now()
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
    
    def register_service(self, app):
        app.add_url_rule("/txion", "txion", self.transaction, methods=['POST'])
        app.add_url_rule("/blocks", "blocks", self.get_blocks, methods=['GET'])
        app.add_url_rule("/mine", "mine", self.mine, methods=['GET'])
        app.add_url_rule("/ping", "ping", self.ping, methods=['GET'])
        app.add_url_rule("/consensus", "consensus", self.consensus, methods=['GET'])

def homepage():
    return render_template("index.html")

def main():
    node.add_url_rule("/index.html", "index.html", homepage, methods=['GET'])
    
    port = 80
    if len(sys.argv) > 1:
        port = int(sys.argv[1])
    
    tc = TinyCoin(port = port)
    tc.register_service(node)
    
    node.run(host='0.0.0.0', port=port)

if __name__ == "__main__":
    main()