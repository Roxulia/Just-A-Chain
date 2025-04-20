import hashlib
import json
from time import time

class Block:
    def __init__(self, index, transactions, proof, previous_hash, timestamp=None, current_hash=None):
        self.index = index
        self.timestamp = timestamp or time()
        self.transactions = transactions
        self.proof = proof
        self.previous_hash = previous_hash
        self.current_hash = current_hash or self.compute_hash()

    def compute_hash(self):
        block_string = json.dumps(self.__dict__, sort_keys=True).encode()
        return hashlib.sha256(block_string).hexdigest()

    def toJSON(self):
        return {'index':self.index,
                'transactions':self.transactions,
                'proof':self.proof,
                'previous_hash':self.previous_hash}