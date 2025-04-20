import json
import os
from urllib.parse import urlparse
import requests,random
import hashlib
import threading,time
from .block import Block
from .transaction import Transaction
from ecdsa import SigningKey, SECP256k1,VerifyingKey

class Blockchain:
    def __init__(self,data_path):
        self.host='0.0.0.0'
        self.port=5000
        self.data_path = data_path
        self.chain = []
        self.current_transactions = []
        self.transaction_cache = set()
        self.seed_node = 'www.ywangancoffee.com'
        self.nodes = set()
        self.balances = {} or self.load_balances()
        self.temp_balances = self.balances
        self.storage_file = os.path.join(self.data_path, 'blockchain.json')
        self.automine = False
        # Load existing blockchain from storage
        self.load_nodes()
        self.load_blockchain()
        if not self.chain:
            # Create the genesis block if the chain is empty
            self.new_block(previous_hash='1', proof=100)
        

        #self.startmine()
    def load_nodes(self):
        file_path = os.path.join(self.data_path, 'nodes.json')
        try:
            with open(file_path, 'r') as file:
                nodes = json.load(file)
                for n in nodes:
                    self.nodes.add(n)
        except FileNotFoundError:
            print("File not found")
        
    def save_nodes(self, nodes):
        file_path = os.path.join(self.data_path, 'nodes.json')
        with open(file_path, 'w') as file:
            json.dump(list(nodes), file)

    def load_balances(self):
        file_path = os.path.join(self.data_path, 'balances.json')
        try:
            with open(file_path, 'r') as file:
                return json.load(file)
        except FileNotFoundError:
            return self.recalculate_balances_from_blockchain()

    def recalculate_balances_from_blockchain(self):
        balances = {'ffff':2000000000}
        if(self.chain != [] and self.valid_chain(self.chain)==False):
            self.resolve_conflicts()
        for block in self.chain:
            for transaction in block.transactions:
                sender = transaction['sender']
                recipient = transaction['recipient']
                amount = transaction['amount']
                balances[sender] = balances.get(sender, 0) - amount
                balances[recipient] = balances.get(recipient, 0) + amount
        self.save_balances(balances)
        return balances

    def save_balances(self, balances):
        file_path = os.path.join(self.data_path, 'balances.json')
        with open(file_path, 'w') as file:
            json.dump(balances, file)

    def save_blockchain(self):
        """
        Save the blockchain to a JSON file.
        """
        with open(self.storage_file, 'w') as f:
            json.dump([block.__dict__ for block in self.chain], f, indent=4)

    def load_blockchain(self):
        """
        Load the blockchain from a JSON file.
        """
        if os.path.exists(self.storage_file):
            with open(self.storage_file, 'r') as f:
                chain_data = json.load(f)
                self.chain = [Block(**block) for block in chain_data]

    def new_block(self, proof, previous_hash=None):
        """
        Create a new Block in the Blockchain and save it to storage.
        """
        block = Block(
            index=len(self.chain) + 1,
            transactions=[t.toJSON() for t in self.current_transactions],
            proof=proof,
            previous_hash=previous_hash or self.last_block.current_hash,
        )
        block.current_hash = block.compute_hash()  # Compute and store the current hash
        self.balances = self.temp_balances
        self.save_balances(self.balances)
        self.current_transactions = []
        self.chain.append(block)
        threading.Thread(target=self.broadcast_block,args=(block,)).start()
        threading.Thread(target=self.clear_cache).start()
        self.save_blockchain()  # Save blockchain after adding a new block
        return block
    
    def add_block(self,transactions):
        Transactions = [Transaction(**t) for t in transactions]
        for t in Transactions:
            if t in self.current_transactions:
                self.current_transactions.remove(t)
        temp_trx = Transactions
        last_trx = [Transaction(**t) for t in self.last_block.transactions]
        for a in Transactions:
            for b in last_trx:
                if a == b :
                    temp_trx.remove(b)
        if len(temp_trx) != 0:
            Transactions = temp_trx
            last_proof = self.last_block.proof
            proof = self.proof_of_work(last_proof)
            block = Block(
                index=len(self.chain) + 1,
                transactions=[t.toJSON() for t in Transactions],
                proof=proof,
                previous_hash=self.last_block.current_hash,
            )
            self.chain.append(block)
            self.save_blockchain()
            print(f'Block added with proof : {proof}')
        else:
            print('The received block already exist')

    def reward_transaction(self,recipient):
        id = '001'
        transaction = Transaction('ffff',recipient,1000,id)
        json_str = json.dumps(transaction.toJSON()).encode()
        byte = os.urandom(32)
        privatekey = SigningKey.from_string(byte, curve=SECP256k1)
        publickey = privatekey.get_verifying_key()
        publickey = publickey.to_string().hex()
        signature = privatekey.sign(json_str).hex()
        return self.new_transaction(transaction.sender,transaction.recipient,transaction.amount,transaction.id,signature,publickey)

    def new_transaction(self, sender, recipient, amount,id,sign,pub_key):
        """
        Creates a new transaction to go into the next mined Block.
        """
        trxcode = f'{id}:{sender}:{recipient}'
        if trxcode in self.transaction_cache:
            return 0
        else:
            self.transaction_cache.add(trxcode)
        transaction = Transaction(sender, recipient, amount,id)
        string = json.dumps(transaction.toJSON()).encode()
        signature = bytes.fromhex(sign)
        publickey = bytes.fromhex(pub_key)
        publickey = VerifyingKey.from_string(publickey, curve=SECP256k1)
        if(not self.verify_sign(publickey,signature,string)):
            return 1
        if self.temp_balances.get(sender, 0) < amount:
            self.transaction_cache.remove(trxcode)
            return 10
        else:
            self.temp_balances[transaction.sender] -= transaction.amount
            self.temp_balances[transaction.recipient] = self.temp_balances.get(transaction.recipient, 0) + transaction.amount
        
        threading.Thread(target= self.broadcast_transaction,args=(transaction,sign,pub_key)).start()
        self.current_transactions.append(transaction)
        
        return self.last_block.index + 1
    
    def get_balance(self,address):
        self.balances = self.recalculate_balances_from_blockchain()
        return self.balances.get(address,0)

    def automineOnOff(self,status):
        if (status == 1):
            self.automine = True
            self.mining_thread = threading.Thread(target=self.mine)
            self.mining_thread.daemon = True
            self.mining_thread.start()
        else:
            self.automine = False
            print("try stopping")

    @property
    def last_block(self):
        return self.chain[-1]

    def proof_of_work(self, last_proof):
        """
        Simple Proof of Work Algorithm:
        - Find a number p' such that hash(pp') contains leading 4 zeroes
        - p is the previous proof, and p' is the new proof
        """
        proof = 0
        while self.valid_proof(last_proof, proof) is False:
            proof += 1
        return proof

    @staticmethod
    def valid_proof(last_proof, proof):
        """
        Validates the Proof: Does hash(last_proof, proof) contain 4 leading zeroes?
        """
        guess = f'{last_proof}{proof}'.encode()
        guess_hash = hashlib.sha256(guess).hexdigest()
        return guess_hash[:4] == "0000"

    def mine(self):
        while self.automine:
            print("running")
            if len(self.current_transactions) > 0:  # Check if there are at least 3 transactions
                if (self.resolve_conflicts()):
                    self.current_transactions = []
                    continue
                last_proof = self.last_block.proof
                proof = self.proof_of_work(last_proof)
                self.new_block(proof)
                print("Block automatically mined with proof:", proof)
            time.sleep(10)
        print("stop mining")

    def register_node(self, address):
        """
        Add a new node to the list of nodes
        """
        if(address != ""):
            parsed_url = urlparse(address)
            self.nodes.add(parsed_url.netloc)
            self.save_nodes(self.nodes)

    def broadcast_transaction(self,Transaction,sign,pub_key):
        data = Transaction.toJSON()
        data['sign'] = sign
        data['pub_key'] = pub_key
        print(data)
        for i in self.nodes:
            if i != f'{self.host}:{self.port}':
                try:
                    response = requests.post(f'http://{i}/transactions/new', json=data)
                except requests.ConnectionError:
                    print(f'Cant connect with : {i}')
    
    def broadcast_block(self,Block):
        data = Block.toJSON()
        print(data)
        for i in self.nodes:
            if i != f'{self.host}:{self.port}':
                try:
                    response = requests.post(f'http://{i}/block/new', json=data)
                except requests.ConnectionError:
                    print(f'Cant connect with : {i}')

    def clear_cache(self):
        time.sleep(120)
        self.transaction_cache=set()

    def verify_sign(self,public_key, signature, message):
    # Verify the signature using the public key
        try:
            public_key.verify(signature, message)
            return True
        except Exception as e:
            return False
        
    def valid_chain(self, chain):
        """
        Determine if a given blockchain is valid
        """
        last_block = chain[0]
        current_index = 1

        while current_index < len(chain):
            block = chain[current_index]
            if block.previous_hash != last_block.current_hash:
                return False
            if not self.valid_proof(last_block.proof, block.proof):
                return False
            last_block = block
            current_index += 1
        return True

    def resolve_conflicts(self):
        """
        This is our Consensus Algorithm, it resolves conflicts by replacing
        our chain with the longest one in the network.
        """
        neighbours = self.nodes
        new_chain = None
        max_length = len(self.chain)

        for node in neighbours:
            try:
                response = requests.get(f'http://{node}/chain')

                if response.status_code == 200:
                    length = response.json()['length']
                    chaindata = response.json()['chain']
                    chain = [Block(**blk) for blk in chaindata]
                    if length > max_length and self.valid_chain(chain):
                        max_length = length
                        new_chain = chain
            except requests.ConnectionError:
                print(f'cannot connect to {node}')
        
        if new_chain:
            self.chain = new_chain
            self.save_blockchain()
            return True

        return False
