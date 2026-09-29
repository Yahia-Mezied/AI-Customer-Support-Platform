from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User, UserRole
from app.schemas.message import MessageCreate, MessageResponse
from app.services import ticket_service

router = APIRouter(prefix="/tickets/{ticket_id}/messages", tags=["Messages"])

@router.get("", response_model=List[MessageResponse])
def get_messages(
    ticket_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Retrieve all messages for a ticket."""
    ticket = ticket_service.get_ticket_by_id(db, ticket_id)
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")

    if current_user.role == UserRole.CUSTOMER.value and ticket.customer_id != current_user.id:
        raise HTTPException(status_code=403, detail="Forbidden")

    messages = ticket_service.get_ticket_messages(db, ticket_id)
    # Enrich response with sender name and role
    result = []
    for msg in messages:
        msg_resp = MessageResponse(
            id=msg.id,
            ticket_id=msg.ticket_id,
            sender_id=msg.sender_id,
            message=msg.message,
            timestamp=msg.timestamp,
            sender_name=msg.sender.name if msg.sender else "Unknown",
            sender_role=msg.sender.role if msg.sender else "user"
        )
        result.append(msg_resp)
    return result

@router.post("", response_model=MessageResponse, status_code=status.HTTP_201_CREATED)
def add_message(
    ticket_id: int,
    message_in: MessageCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Post a new message in a ticket conversation."""
    ticket = ticket_service.get_ticket_by_id(db, ticket_id)
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")

    if current_user.role == UserRole.CUSTOMER.value and ticket.customer_id != current_user.id:
        raise HTTPException(status_code=403, detail="Forbidden")

    msg = ticket_service.add_ticket_message(
        db=db,
        ticket_id=ticket_id,
        sender_id=current_user.id,
        message_text=message_in.message
    )
    
    return MessageResponse(
        id=msg.id,
        ticket_id=msg.ticket_id,
        sender_id=msg.sender_id,
        message=msg.message,
        timestamp=msg.timestamp,
        sender_name=current_user.name,
        sender_role=current_user.role
    )
