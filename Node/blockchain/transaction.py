import json
class Transaction:
    def __init__(self, sender, recipient, amount,id):
        self.id = id
        self.sender = sender
        self.recipient = recipient
        self.amount = amount

    def toJSON(self):
        return {"sender":self.sender,"recipient" : self.recipient,"amount":self.amount,"id" : self.id}
    
    def __eq__(self, value: object) -> bool:
        if (self.id == value.id and self.sender == value.sender and self.recipient == value.recipient and self.amount==value.amount):
            return True
        return False