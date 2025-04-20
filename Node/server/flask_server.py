from flask import Flask, jsonify, request
from blockchain.blockchain import Blockchain

class BlockchainServer:
    def __init__(self,blockchain, host='0.0.0.0', port=5000):
        self.app = Flask(__name__)
        self.blockchain = blockchain
        self.host = host
        self.port = port
        self.setup_routes()

    def setup_routes(self):
        self.app.add_url_rule('/mine', 'mine', self.mine, methods=['GET'])
        self.app.add_url_rule('/transactions/new', 'new_transaction', self.new_transaction, methods=['POST'])
        self.app.add_url_rule('/chain', 'full_chain', self.full_chain, methods=['GET'])
        self.app.add_url_rule('/nodes/register', 'register_nodes', self.register_nodes, methods=['POST'])
        self.app.add_url_rule('/nodes/resolve', 'consensus', self.consensus, methods=['GET'])
        self.app.add_url_rule('/nodes', 'nodes', self.get_nodes, methods=['GET'])
        self.app.add_url_rule('/reward', 'reward', self.reward, methods=['POST'])
        self.app.add_url_rule('/balance','balance',self.get_balances,methods = ['POST'])
        self.app.add_url_rule('/check','check',self.check,methods=['GET'])
        self.app.add_url_rule('/block/new', 'new_block', self.new_block, methods=['POST'])

    def check(self):
        response = {'message':"I am OK"}
        return jsonify(response),200
    
    def mine(self):
        last_proof = self.blockchain.last_block.proof
        proof = self.blockchain.proof_of_work(last_proof)
        block = self.blockchain.new_block(proof)
        response = {
            'message': "New Block Forged",
            'index': block.index,
            'transactions': block.transactions,
            'proof': block.proof,
            'previous_hash': block.previous_hash,
        }
        return jsonify(response), 200

    def new_transaction(self):
        values = request.get_json()
        required = ['sender', 'recipient', 'amount','id','sign','pub_key']
        if not all(k in values for k in required):
            return 'Missing values', 400

        index = self.blockchain.new_transaction(values['sender'], values['recipient'], values['amount'],values['id'],values['sign'],values['pub_key'])
        if index == 0:
            response = {'message' : 'Transaction is already in cache'}
            return jsonify(response), 204
        elif index == 1:
            response = {'message' : 'Unvalid Transaction'}
            return jsonify(response), 203
        elif index == 10:
            response = {'message' : 'Balance Insufficient'}
            return jsonify(response), 202
        else:
            response = {'message': f'Transaction will be added to Block {index}'}
            return jsonify(response), 201

    def new_block(self):
        values = request.get_json()
        self.blockchain.add_block(values['transactions'])
        response = {'message':'done adding Block'}
        return jsonify(response),200

    def full_chain(self):
        response = {
            'chain': [block.__dict__ for block in self.blockchain.chain],
            'length': len(self.blockchain.chain),
        }
        return jsonify(response), 200

    def register_nodes(self):
        values = request.get_json()
        nodes = values.get('node')
        print(nodes)
        if nodes is None:
            return "Error: Please supply a valid list of nodes", 400
        for node in nodes:
            self.blockchain.register_node(node)
        response = {
            'message': 'New nodes have been added',
            'total_nodes': list(self.blockchain.nodes),
        }
        return jsonify(response), 201

    def consensus(self):
        replaced = self.blockchain.resolve_conflicts()
        if replaced:
            response = {
                'message': 'Our chain was replaced',
                'new_chain': [block.__dict__ for block in self.blockchain.chain]
            }
        else:
            response = {
                'message': 'Our chain is authoritative',
                'chain': [block.__dict__ for block in self.blockchain.chain]
            }
        return jsonify(response), 200
    
    def get_nodes(self):
        response = {'links' : list(self.blockchain.nodes)}
        return jsonify(response),200
    
    def get_balances(self):
        values = request.get_json()
        response = {'balance' : self.blockchain.get_balance(values['address'])}
        return jsonify(response),200
    
    def reward(self):
        values = request.get_json()
        index = self.blockchain.reward_transaction(values['recipient'])
        if index == 0:
            response = {'message' : 'Transaction is already in cache'}
            return jsonify(response), 204
        elif index == 1:
            response = {'message' : 'Unvalid Transaction'}
            return jsonify(response), 203
        elif index == 10:
            response = {'message' : 'Balance Insufficient'}
            return jsonify(response), 202
        else:
            response = {'message': f'Transaction will be added to Block {index}'}
            return jsonify(response), 201
    
    def run(self):
        self.app.run(host=self.host, port=self.port)

