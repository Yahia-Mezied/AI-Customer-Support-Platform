from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel
from app.schemas.user import UserResponse
from app.schemas.message import MessageResponse

class TicketBase(BaseModel):
    subject: str
    description: str
    category: Optional[str] = "General Inquiry"
    priority: Optional[str] = "Medium"

class TicketCreate(TicketBase):
    pass

class TicketUpdate(BaseModel):
    subject: Optional[str] = None
    description: Optional[str] = None
    category: Optional[str] = None
    priority: Optional[str] = None
    status: Optional[str] = None
    assigned_agent_id: Optional[int] = None

class TicketEscalateRequest(BaseModel):
    reason: Optional[str] = "Customer requested human escalation"

class TicketAIClassification(BaseModel):
    category: Optional[str] = None
    priority: Optional[str] = None
    summary: Optional[str] = None
    suggested_action: Optional[str] = None

class TicketResponse(TicketBase):
    id: int
    customer_id: int
    assigned_agent_id: Optional[int] = None
    status: str
    
    # AI Fields
    ai_category: Optional[str] = None
    ai_priority: Optional[str] = None
    ai_summary: Optional[str] = None
    ai_suggested_action: Optional[str] = None

    created_at: datetime
    updated_at: datetime
    resolution_date: Optional[datetime] = None

    customer: Optional[UserResponse] = None
    assigned_agent: Optional[UserResponse] = None
    messages: Optional[List[MessageResponse]] = []

    class Config:
        from_attributes = True
