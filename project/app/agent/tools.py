"""Backend tools for the LangChain/LangGraph AI Agent.

These functions provide direct integration with the database and business logic
for the 6 required tools specified in Section 8 of the project requirements,
plus conversational message tools.
"""

from typing import List, Dict, Any, Optional
from langchain_core.tools import tool
from app.core.database import SessionLocal
from app.models.user import User, UserRole
from app.models.ticket import TicketPriority, TicketStatus
from app.schemas.ticket import TicketCreate, TicketUpdate
from app.services import ticket_service, webhook_service
import asyncio

def build_tools(current_user: User, auth_token: Optional[str] = None):
    """Factory to construct LangChain tools bound to the current authenticated user context."""
    user_id = current_user.id
    user_role = current_user.role

    @tool
    def get_customer_tickets(status: Optional[str] = None) -> str:
        """Get all support tickets belonging to the current customer.
        Optionally filter by status (e.g. 'open', 'in_progress', 'resolved')."""
        db = SessionLocal()
        try:
            user = db.query(User).filter(User.id == user_id).first()
            if not user:
                return "Customer profile not found."
            tickets = ticket_service.get_tickets_for_user(db, user, status=status)
            if not tickets:
                return "You currently have no support tickets." if not status else f"You have no tickets with status '{status}'."
            summary = []
            for t in tickets:
                summary.append(
                    f"- Ticket #{t.id}: {t.subject} | Status: {t.status} | Priority: {t.priority} | Category: {t.category}"
                )
            return "Here are your tickets:\n" + "\n".join(summary)
        except Exception as e:
            return f"Error retrieving tickets: {str(e)}"
        finally:
            db.close()

    @tool
    def get_ticket_details(ticket_id: int) -> str:
        """Get complete details and conversation history for a specific ticket ID."""
        db = SessionLocal()
        try:
            ticket = ticket_service.get_ticket_by_id(db, ticket_id)
            if not ticket:
                return f"Ticket #{ticket_id} was not found."
            if user_role == UserRole.CUSTOMER.value and ticket.customer_id != user_id:
                return f"Permission denied: You do not have permission to view ticket #{ticket_id}."
            
            messages = ticket_service.get_ticket_messages(db, ticket_id)
            msg_history = "\n".join([f"  * {m.sender.name if m.sender else 'User'}: {m.message}" for m in messages[-5:]]) if messages else "  (No messages yet)"
            
            return (
                f"Ticket #{ticket.id}: {ticket.subject}\n"
                f"Status: {ticket.status}\n"
                f"Priority: {ticket.priority}\n"
                f"Category: {ticket.category}\n"
                f"Description: {ticket.description}\n"
                f"Created: {ticket.created_at}\n"
                f"Recent Messages:\n{msg_history}"
            )
        except Exception as e:
            return f"Error retrieving ticket details: {str(e)}"
        finally:
            db.close()

    @tool
    def create_ticket(subject: str, description: str, category: str = "General Inquiry", priority: str = "Medium") -> str:
        """Create a new support ticket.
        Category options: Technical Issue, Account Issue, Billing, Product Issue, General Inquiry.
        Priority options: Low, Medium, High, Critical."""
        db = SessionLocal()
        try:
            ticket_in = TicketCreate(
                subject=subject,
                description=description,
                category=category,
                priority=priority
            )
            ticket = ticket_service.create_ticket(db, customer_id=user_id, ticket_in=ticket_in)
            
            # Asynchronously trigger n8n notification if possible
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    asyncio.create_task(webhook_service.notify_ticket_created({
                        "event": "ticket_created",
                        "ticket_id": ticket.id,
                        "customer_id": user_id,
                        "subject": ticket.subject,
                        "category": ticket.category,
                        "priority": ticket.priority,
                        "status": ticket.status
                    }))
            except Exception:
                pass

            return f"Success! Support ticket #{ticket.id} ('{ticket.subject}') has been created with status '{ticket.status}' and priority '{ticket.priority}'."
        except Exception as e:
            return f"Error creating support ticket: {str(e)}"
        finally:
            db.close()

    @tool
    def check_ticket_status(ticket_id: int) -> str:
        """Check the current status and priority of a specific ticket ID."""
        db = SessionLocal()
        try:
            ticket = ticket_service.get_ticket_by_id(db, ticket_id)
            if not ticket:
                return f"Ticket #{ticket_id} was not found."
            if user_role == UserRole.CUSTOMER.value and ticket.customer_id != user_id:
                return f"Permission denied: You do not have permission to view ticket #{ticket_id}."
            return f"Ticket #{ticket.id} ('{ticket.subject}') is currently '{ticket.status}' with priority '{ticket.priority}'."
        except Exception as e:
            return f"Error checking ticket status: {str(e)}"
        finally:
            db.close()

    @tool
    def update_ticket(ticket_id: int, status: Optional[str] = None, priority: Optional[str] = None) -> str:
        """Update permitted ticket information like status or priority."""
        db = SessionLocal()
        try:
            ticket = ticket_service.get_ticket_by_id(db, ticket_id)
            if not ticket:
                return f"Ticket #{ticket_id} not found."
            if user_role == UserRole.CUSTOMER.value and ticket.customer_id != user_id:
                return f"Permission denied: You can only update your own tickets."
            
            update_in = TicketUpdate(status=status, priority=priority)
            updated = ticket_service.update_ticket(db, ticket_id, update_in, current_user)
            return f"Ticket #{ticket_id} updated successfully. Status: {updated.status}, Priority: {updated.priority}."
        except Exception as e:
            return f"Error updating ticket: {str(e)}"
        finally:
            db.close()

    @tool
    def escalate_ticket(ticket_id: int, reason: str = "Customer requested human escalation") -> str:
        """Escalate a ticket to human support and mark as Critical priority.
        Use this when: issue is critical, customer is frustrated, or the problem cannot be resolved by AI."""
        db = SessionLocal()
        try:
            ticket = ticket_service.get_ticket_by_id(db, ticket_id)
            if not ticket:
                return f"Ticket #{ticket_id} was not found."
            if user_role == UserRole.CUSTOMER.value and ticket.customer_id != user_id:
                return f"Permission denied for ticket #{ticket_id}."

            escalated = ticket_service.escalate_ticket(db, ticket_id, reason, current_user)

            # Trigger n8n webhook
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    asyncio.create_task(webhook_service.notify_ticket_escalated({
                        "event": "ticket_escalated",
                        "ticket_id": escalated.id,
                        "subject": escalated.subject,
                        "priority": escalated.priority,
                        "reason": reason
                    }))
            except Exception:
                pass

            return f"Ticket #{ticket_id} has been escalated to Critical priority. A human support agent has been notified and will assist shortly. Reason: {reason}"
        except Exception as e:
            return f"Error escalating ticket: {str(e)}"
        finally:
            db.close()

    @tool
    def add_message_to_ticket(ticket_id: int, message: str) -> str:
        """Add a new message or reply to an existing ticket conversation."""
        db = SessionLocal()
        try:
            ticket = ticket_service.get_ticket_by_id(db, ticket_id)
            if not ticket:
                return f"Ticket #{ticket_id} not found."
            if user_role == UserRole.CUSTOMER.value and ticket.customer_id != user_id:
                return f"Permission denied for ticket #{ticket_id}."

            msg = ticket_service.add_ticket_message(db, ticket_id, user_id, message)
            return f"Message successfully recorded in Ticket #{ticket_id}."
        except Exception as e:
            return f"Error adding message to ticket: {str(e)}"
        finally:
            db.close()

    return [
        get_customer_tickets,
        get_ticket_details,
        create_ticket,
        check_ticket_status,
        update_ticket,
        escalate_ticket,
        add_message_to_ticket,
    ]


# Backward compatible standalone functions
def tool_get_customer_tickets(customer_id: int) -> List[Dict[str, Any]]:
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.id == customer_id).first()
        if not user:
            return [{"error": "Customer not found"}]
        tickets = ticket_service.get_tickets_for_user(db, user)
        return [
            {
                "ticket_id": t.id,
                "subject": t.subject,
                "category": t.category,
                "status": t.status,
                "priority": t.priority,
                "created_at": str(t.created_at)
            }
            for t in tickets
        ]
    finally:
        db.close()

def tool_get_ticket_details(ticket_id: int) -> Dict[str, Any]:
    db = SessionLocal()
    try:
        ticket = ticket_service.get_ticket_by_id(db, ticket_id)
        if not ticket:
            return {"error": f"Ticket #{ticket_id} not found"}
        messages = ticket_service.get_ticket_messages(db, ticket_id)
        return {
            "ticket_id": ticket.id,
            "customer_id": ticket.customer_id,
            "subject": ticket.subject,
            "description": ticket.description,
            "category": ticket.category,
            "status": ticket.status,
            "priority": ticket.priority,
            "created_at": str(ticket.created_at),
            "messages_count": len(messages),
            "messages": [
                {"sender": m.sender.name if m.sender else "User", "text": m.message}
                for m in messages
            ]
        }
    finally:
        db.close()

def tool_create_ticket(customer_id: int, subject: str, description: str, category: str = "General Inquiry") -> Dict[str, Any]:
    db = SessionLocal()
    try:
        ticket_in = TicketCreate(
            subject=subject,
            description=description,
            category=category,
            priority=TicketPriority.MEDIUM.value
        )
        ticket = ticket_service.create_ticket(db, customer_id=customer_id, ticket_in=ticket_in)
        return {
            "success": True,
            "ticket_id": ticket.id,
            "subject": ticket.subject,
            "status": ticket.status,
            "message": f"Support ticket #{ticket.id} created successfully."
        }
    finally:
        db.close()

def tool_check_ticket_status(ticket_id: int) -> Dict[str, Any]:
    db = SessionLocal()
    try:
        ticket = ticket_service.get_ticket_by_id(db, ticket_id)
        if not ticket:
            return {"error": f"Ticket #{ticket_id} not found"}
        return {
            "ticket_id": ticket.id,
            "subject": ticket.subject,
            "status": ticket.status,
            "priority": ticket.priority,
            "updated_at": str(ticket.updated_at)
        }
    finally:
        db.close()

def tool_update_ticket(ticket_id: int, status: Optional[str] = None, priority: Optional[str] = None) -> Dict[str, Any]:
    db = SessionLocal()
    try:
        ticket = ticket_service.get_ticket_by_id(db, ticket_id)
        if not ticket:
            return {"error": f"Ticket #{ticket_id} not found"}
        if status:
            ticket.status = status
        if priority:
            ticket.priority = priority
        db.commit()
        db.refresh(ticket)
        return {
            "success": True,
            "ticket_id": ticket.id,
            "new_status": ticket.status,
            "new_priority": ticket.priority
        }
    finally:
        db.close()

def tool_escalate_ticket(ticket_id: int, reason: str = "Unresolved customer issue") -> Dict[str, Any]:
    db = SessionLocal()
    try:
        ticket = ticket_service.get_ticket_by_id(db, ticket_id)
        if not ticket:
            return {"error": f"Ticket #{ticket_id} not found"}
        ticket.priority = TicketPriority.CRITICAL.value
        msg = ticket_service.add_ticket_message(
            db=db,
            ticket_id=ticket.id,
            sender_id=ticket.customer_id,
            message_text=f"[AI ESCALATION] Ticket escalated to Critical. Reason: {reason}"
        )
        db.commit()
        db.refresh(ticket)
        return {
            "success": True,
            "ticket_id": ticket.id,
            "priority": ticket.priority,
            "escalation_note": reason
        }
    finally:
        db.close()
