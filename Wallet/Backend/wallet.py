import os
import hashlib,requests,json
from mnemonic import Mnemonic
from ecdsa import SigningKey, SECP256k1
import random
class Wallet:
    def __init__(self, mnemonic_phrase=None,balance = 0):
        self.mnemonic = Mnemonic("english")
        self.balance = balance
        if mnemonic_phrase:
            self.key_phrase = mnemonic_phrase
        else:
            self.key_phrase = self.mnemonic.generate(strength=128)
        self.private_key = self._generate_private_key(self.key_phrase)
        self.public_key = self.private_key.get_verifying_key()
        self.address = self._generate_address()

    def _generate_private_key(self, key_phrase):
        seed = self.mnemonic.to_seed(key_phrase)
        return SigningKey.from_string(seed[:32], curve=SECP256k1)
    
    def _generate_address(self):
        public_key_bytes = self.public_key.to_string()
        address = hashlib.sha256(public_key_bytes).hexdigest()
        return address[:40]  # You can truncate or modify the length as needed

    def sign_transaction(self, transaction_data):
        return self.private_key.sign(transaction_data.encode())

    def verify_transaction(self, transaction_data, signature):
        return self.public_key.verify(signature, transaction_data.encode())
    
    
    def send_transaction(self,recipient,amount,nodes=[]):
        trxData = {'sender' : self.address,
                   'recipient' : recipient,
                   'amount' : amount,
                   'id': random.randint(1,1000)
            }
        string = json.dumps(trxData)
        signature = self.sign_transaction(string)
        trxData['sign'] = signature.hex()
        trxData['pub_key'] = self.public_key.to_string().hex()
        for node in nodes:
            try:
                response = requests.post(f'{node}/transactions/new',json=trxData)
                if(response.status_code == 201):
                    return "transaction successfully added balance will update when validation is complete"
                elif response.status_code == 202:
                    return "Insufficient Balance"
                else:
                    continue
            except requests.ConnectionError:
                continue
        return "Error making Transaction"
    
    def request_balance(self,nodes=[]):
        for node in nodes:
            try:
                response = requests.post(f'{node}/balance',json={'address':self.address})
                if response.status_code == 200:
                    self.balance = response.json()['balance']
                    return True
            except requests.ConnectionError:
                continue
        return False
    
    def __eq__(self, value: object) -> bool:
        if(isinstance(value,Wallet) and self.address == value.address):
            return True
        return False

    def toJSON(self):
        return {'mnemonic' : self.key_phrase,'balance':self.balance}