from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.security import get_current_user, require_role
from app.models.user import User, UserRole
from app.models.ticket import TicketPriority, TicketStatus
from app.schemas.ticket import TicketCreate, TicketUpdate, TicketResponse, TicketEscalateRequest
from app.services import ticket_service, webhook_service

router = APIRouter(prefix="/tickets", tags=["Tickets"])

@router.get("", response_model=List[TicketResponse])
def get_tickets(
    status: Optional[str] = None,
    category: Optional[str] = None,
    priority: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Retrieve tickets accessible to the current user."""
    return ticket_service.get_tickets_for_user(
        db=db, 
        user=current_user, 
        status=status, 
        category=category, 
        priority=priority
    )

@router.post("", response_model=TicketResponse, status_code=status.HTTP_201_CREATED)
def create_ticket(
    ticket_in: TicketCreate,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new ticket and notify n8n workflow."""
    ticket = ticket_service.create_ticket(db, customer_id=current_user.id, ticket_in=ticket_in)
    
    # Trigger n8n New Ticket Notification asynchronously
    ticket_payload = {
        "event": "ticket_created",
        "ticket_id": ticket.id,
        "customer_id": current_user.id,
        "customer_name": current_user.name,
        "customer_email": current_user.email,
        "subject": ticket.subject,
        "description": ticket.description,
        "category": ticket.category,
        "priority": ticket.priority,
        "status": ticket.status,
        "created_at": str(ticket.created_at)
    }
    background_tasks.add_task(webhook_service.notify_ticket_created, ticket_payload)

    return ticket

@router.get("/{ticket_id}", response_model=TicketResponse)
def get_ticket(
    ticket_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get single ticket details."""
    ticket = ticket_service.get_ticket_by_id(db, ticket_id)
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    
    # Check authorization
    if current_user.role == UserRole.CUSTOMER.value and ticket.customer_id != current_user.id:
        raise HTTPException(status_code=403, detail="Forbidden")

    return ticket

@router.put("/{ticket_id}", response_model=TicketResponse)
@router.patch("/{ticket_id}", response_model=TicketResponse)
def update_ticket(
    ticket_id: int,
    ticket_in: TicketUpdate,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update ticket properties and trigger status webhooks."""
    original_ticket = ticket_service.get_ticket_by_id(db, ticket_id)
    if not original_ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")

    old_priority = original_ticket.priority
    old_status = original_ticket.status

    updated = ticket_service.update_ticket(db, ticket_id, ticket_in, current_user)

    # Check for escalation or critical status
    if updated.priority == TicketPriority.CRITICAL.value and old_priority != TicketPriority.CRITICAL.value:
        background_tasks.add_task(
            webhook_service.notify_ticket_escalated,
            {
                "event": "ticket_escalated",
                "ticket_id": updated.id,
                "subject": updated.subject,
                "priority": updated.priority,
                "status": updated.status,
                "updated_by": current_user.name
            }
        )

    # Check for resolution
    if updated.status == TicketStatus.RESOLVED.value and old_status != TicketStatus.RESOLVED.value:
        background_tasks.add_task(
            webhook_service.notify_ticket_resolved,
            {
                "event": "ticket_resolved",
                "ticket_id": updated.id,
                "subject": updated.subject,
                "resolved_at": str(updated.resolution_date),
                "resolved_by": current_user.name
            }
        )

    return updated

@router.post("/{ticket_id}/escalate", response_model=TicketResponse)
def escalate_ticket(
    ticket_id: int,
    background_tasks: BackgroundTasks,
    req: Optional[TicketEscalateRequest] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Explicitly escalate a ticket and trigger n8n escalation workflow."""
    reason = req.reason if (req and req.reason) else "Customer requested human escalation"
    ticket = ticket_service.escalate_ticket(db, ticket_id, reason, current_user)
    
    background_tasks.add_task(
        webhook_service.notify_ticket_escalated,
        {
            "event": "ticket_escalated",
            "ticket_id": ticket.id,
            "subject": ticket.subject,
            "priority": ticket.priority,
            "reason": reason,
            "escalated_by": current_user.name
        }
    )
    return ticket

@router.delete("/{ticket_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_ticket(
    ticket_id: int,
    current_user: User = Depends(require_role([UserRole.ADMIN.value])),
    db: Session = Depends(get_db)
):
    """Delete ticket (Admin only)."""
    ticket = ticket_service.get_ticket_by_id(db, ticket_id)
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    db.delete(ticket)
    db.commit()
    return None
