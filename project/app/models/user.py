import enum
from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.core.database import Base

class UserRole(str, enum.Enum):
    CUSTOMER = "customer"
    AGENT = "agent"
    ADMIN = "admin"

class AccountStatus(str, enum.Enum):
    ACTIVE = "active"
    DISABLED = "disabled"
    SUSPENDED = "suspended"

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    email = Column(String(255), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    role = Column(String(20), default=UserRole.CUSTOMER.value, nullable=False)
    account_status = Column(String(20), default=AccountStatus.ACTIVE.value, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Relationships
    tickets = relationship("Ticket", foreign_keys="[Ticket.customer_id]", back_populates="customer", cascade="all, delete-orphan")
    assigned_tickets = relationship("Ticket", foreign_keys="[Ticket.assigned_agent_id]", back_populates="assigned_agent")
    messages = relationship("Message", back_populates="sender", cascade="all, delete-orphan")
