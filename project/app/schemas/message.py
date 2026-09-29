from datetime import datetime
from typing import Optional
from pydantic import BaseModel

class MessageCreate(BaseModel):
    message: str

class MessageResponse(BaseModel):
    id: int
    ticket_id: int
    sender_id: int
    message: str
    timestamp: datetime
    sender_name: Optional[str] = None
    sender_role: Optional[str] = None

    class Config:
        from_attributes = True
