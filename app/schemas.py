from pydantic import BaseModel, Field
from typing import List

class Product(BaseModel):
    id: int=Field(serialization_alias="_id")
    name: str
    price: int
    qty: int
    status: str
    category: str
    description: str

class Denomination(BaseModel):
    value: int
    count: int

class CashDrawer(BaseModel):
    currency: str=Field(serialization_alias="_id")
    denoms: List[Denomination]

class ChangeItem(BaseModel):
    value: int
    count: int

class Transaction(BaseModel):
    id: str = Field(serialization_alias="_id")
    snack_id: int
    price: int
    cash_in: int
    change: List[ChangeItem]
    status: str
    ts: float | None = None