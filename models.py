from pydantic import BaseModel

class User(BaseModel):
    name: str
    pin: str

class Transfer(BaseModel):
    sender_name: str
    recipient_name: str
    amount: float

class UserUpdate(BaseModel):
    pin: str
    balance: float

class UserIdentifier(BaseModel):
    pin: str