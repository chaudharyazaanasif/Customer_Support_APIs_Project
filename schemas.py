import datetime

from pydantic import BaseModel
from pydantic.v1 import EmailStr


class TicketInput(BaseModel):
    id: int
    customer_name: str
    email:str
    subject: str
    description:str
    category: str
    priority: str
    status:str
    created_at: str