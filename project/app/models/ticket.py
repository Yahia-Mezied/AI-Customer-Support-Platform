import enum
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.core.database import Base

class TicketCategory(str, enum.Enum):
    TECHNICAL = "Technical Issue"
    ACCOUNT = "Account Issue"
    BILLING = "Billing"
    PRODUCT = "Product Issue"
    GENERAL = "General Inquiry"

class TicketPriority(str, enum.Enum):
    LOW = "Low"
    MEDIUM = "Medium"
    HIGH = "High"
    CRITICAL = "Critical"

class TicketStatus(str, enum.Enum):
    OPEN = "Open"
    IN_PROGRESS = "In Progress"
    WAITING_FOR_CUSTOMER = "Waiting for Customer"
    RESOLVED = "Resolved"
    CLOSED = "Closed"

class Ticket(Base):
    __tablename__ = "tickets"

    id = Column(Integer, primary_key=True, index=True)
    customer_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    assigned_agent_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    
    subject = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    category = Column(String(50), default=TicketCategory.GENERAL.value, nullable=False)
    priority = Column(String(20), default=TicketPriority.MEDIUM.value, nullable=False)
    status = Column(String(30), default=TicketStatus.OPEN.value, nullable=False)
    
    # AI Classification fields (from PDF spec section 13)
    ai_category = Column(String(50), nullable=True)
    ai_priority = Column(String(20), nullable=True)
    ai_summary = Column(Text, nullable=True)
    ai_suggested_action = Column(Text, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    resolution_date = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    customer = relationship("User", foreign_keys=[customer_id], back_populates="tickets")
    assigned_agent = relationship("User", foreign_keys=[assigned_agent_id], back_populates="assigned_tickets")
    messages = relationship("Message", back_populates="ticket", cascade="all, delete-orphan", order_by="Message.timestamp")
