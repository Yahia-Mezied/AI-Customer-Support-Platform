from datetime import datetime, timezone
from typing import Optional, List
from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import desc, func
from app.models.ticket import Ticket, TicketPriority, TicketStatus
from app.models.message import Message
from app.models.user import User, UserRole
from app.schemas.ticket import TicketCreate, TicketUpdate

def classify_ticket_heuristically(subject: str, description: str):
    """Fallback quick classifier for ticket creation metadata."""
    text_lower = f"{subject} {description}".lower()
    if any(w in text_lower for w in ["bill", "payment", "charge", "refund", "invoice"]):
        cat = "Billing"
        prio = "High"
    elif any(w in text_lower for w in ["password", "login", "auth", "account", "locked"]):
        cat = "Account Issue"
        prio = "High"
    elif any(w in text_lower for w in ["bug", "error", "crash", "failed", "broken", "500"]):
        cat = "Technical Issue"
        prio = "High"
    elif any(w in text_lower for w in ["product", "feature", "item"]):
        cat = "Product Issue"
        prio = "Medium"
    else:
        cat = "General Inquiry"
        prio = "Medium"
    summary = (description[:120] if description else subject)
    action = f"Assign to {cat} support specialist for review."
    return cat, prio, summary, action

def create_ticket(db: Session, customer_id: int, ticket_in: TicketCreate) -> Ticket:
    """Create a new ticket for a customer and store initial AI classification metadata."""
    ai_cat, ai_prio, ai_sum, ai_act = classify_ticket_heuristically(ticket_in.subject, ticket_in.description)

    ticket = Ticket(
        customer_id=customer_id,
        subject=ticket_in.subject,
        description=ticket_in.description,
        category=ticket_in.category or ai_cat,
        priority=ticket_in.priority or ai_prio,
        status=TicketStatus.OPEN.value,
        ai_category=ai_cat,
        ai_priority=ai_prio,
        ai_summary=ai_sum,
        ai_suggested_action=ai_act
    )
    db.add(ticket)
    db.commit()
    db.refresh(ticket)
    return ticket

def get_ticket_by_id(db: Session, ticket_id: int) -> Optional[Ticket]:
    """Retrieve ticket by ID."""
    return db.query(Ticket).filter(Ticket.id == ticket_id).first()

def get_tickets_for_user(
    db: Session, 
    user: User, 
    status: Optional[str] = None,
    category: Optional[str] = None,
    priority: Optional[str] = None
) -> List[Ticket]:
    """Retrieve tickets filtered by user role and case-insensitive query parameters."""
    query = db.query(Ticket)
    
    if user.role == UserRole.CUSTOMER.value:
        query = query.filter(Ticket.customer_id == user.id)
    elif user.role == UserRole.AGENT.value:
        # Agent sees assigned tickets or unassigned open tickets
        query = query.filter(
            (Ticket.assigned_agent_id == user.id) | (Ticket.assigned_agent_id.is_(None))
        )
    # Admin sees all tickets

    if status:
        query = query.filter(func.lower(Ticket.status) == status.strip().lower())
    if category:
        query = query.filter(func.lower(Ticket.category) == category.strip().lower())
    if priority:
        query = query.filter(func.lower(Ticket.priority) == priority.strip().lower())

    return query.order_by(desc(Ticket.created_at)).all()

def update_ticket(
    db: Session, 
    ticket_id: int, 
    ticket_update: TicketUpdate, 
    user: User
) -> Ticket:
    """Update ticket fields with role-based checks."""
    ticket = get_ticket_by_id(db, ticket_id)
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")

    # Access control
    if user.role == UserRole.CUSTOMER.value:
        if ticket.customer_id != user.id:
            raise HTTPException(status_code=403, detail="Not authorized to edit this ticket")

    update_dict = ticket_update.model_dump(exclude_unset=True)
    
    # Customers cannot reassign tickets to arbitrary agents
    if user.role == UserRole.CUSTOMER.value and "assigned_agent_id" in update_dict:
        del update_dict["assigned_agent_id"]

    for field, value in update_dict.items():
        if value is not None:
            setattr(ticket, field, value)
            if field == "status" and value == TicketStatus.RESOLVED.value:
                ticket.resolution_date = datetime.now(timezone.utc)

    db.commit()
    db.refresh(ticket)
    return ticket

def escalate_ticket(db: Session, ticket_id: int, reason: str, user: User) -> Ticket:
    """Escalate a ticket to Critical priority."""
    ticket = get_ticket_by_id(db, ticket_id)
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")

    ticket.priority = TicketPriority.CRITICAL.value
    
    # Add a system/internal note message about escalation
    escalation_message = Message(
        ticket_id=ticket.id,
        sender_id=user.id,
        message=f"[TICKET ESCALATED] Reason: {reason}"
    )
    db.add(escalation_message)
    db.commit()
    db.refresh(ticket)
    return ticket

def add_ticket_message(db: Session, ticket_id: int, sender_id: int, message_text: str) -> Message:
    """Add a message to a ticket conversation."""
    message = Message(
        ticket_id=ticket_id,
        sender_id=sender_id,
        message=message_text
    )
    db.add(message)
    db.commit()
    db.refresh(message)
    return message

def get_ticket_messages(db: Session, ticket_id: int) -> List[Message]:
    """Retrieve all messages for a ticket."""
    return db.query(Message).filter(Message.ticket_id == ticket_id).order_by(Message.timestamp.asc()).all()
