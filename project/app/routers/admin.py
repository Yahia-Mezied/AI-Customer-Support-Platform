from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.core.database import get_db
from app.core.security import require_role
from app.models.user import User, UserRole, AccountStatus
from app.models.ticket import Ticket, TicketStatus, TicketPriority
from app.schemas.user import UserResponse, UserCreate, UserUpdate

router = APIRouter(prefix="/admin", tags=["Admin & Analytics"])

@router.get("/stats")
def get_admin_statistics(
    current_user: User = Depends(require_role([UserRole.ADMIN.value])),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """Retrieve full dashboard statistics matching project requirements."""
    total_tickets = db.query(Ticket).count()
    open_tickets = db.query(Ticket).filter(Ticket.status == TicketStatus.OPEN.value).count()
    in_progress = db.query(Ticket).filter(Ticket.status == TicketStatus.IN_PROGRESS.value).count()
    resolved = db.query(Ticket).filter(Ticket.status == TicketStatus.RESOLVED.value).count()
    closed = db.query(Ticket).filter(Ticket.status == TicketStatus.CLOSED.value).count()
    critical = db.query(Ticket).filter(Ticket.priority == TicketPriority.CRITICAL.value).count()

    # Category counts
    category_counts_query = (
        db.query(Ticket.category, func.count(Ticket.id))
        .group_by(Ticket.category)
        .all()
    )
    tickets_by_category = {cat: count for cat, count in category_counts_query}

    # Tickets assigned to agents
    agent_counts_query = (
        db.query(User.name, func.count(Ticket.id))
        .join(Ticket, Ticket.assigned_agent_id == User.id)
        .group_by(User.name)
        .all()
    )
    tickets_by_agent = {agent: count for agent, count in agent_counts_query}

    return {
        "total_tickets": total_tickets,
        "open_tickets": open_tickets,
        "in_progress_tickets": in_progress,
        "resolved_tickets": resolved,
        "closed_tickets": closed,
        "critical_tickets": critical,
        "tickets_by_category": tickets_by_category,
        "tickets_by_agent": tickets_by_agent
    }

@router.get("/users", response_model=List[UserResponse])
def get_all_users(
    role: Optional[str] = None,
    current_user: User = Depends(require_role([UserRole.ADMIN.value])),
    db: Session = Depends(get_db)
):
    """List users in the system with optional role filter."""
    query = db.query(User)
    if role:
        query = query.filter(User.role == role)
    return query.all()

@router.get("/agents", response_model=List[UserResponse])
def get_all_agents(
    current_user: User = Depends(require_role([UserRole.ADMIN.value, UserRole.AGENT.value])),
    db: Session = Depends(get_db)
):
    """List all support agents for assignment."""
    return db.query(User).filter(User.role == UserRole.AGENT.value).all()

@router.post("/users", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def create_user_by_admin(
    user_in: UserCreate,
    current_user: User = Depends(require_role([UserRole.ADMIN.value])),
    db: Session = Depends(get_db)
):
    """Admin endpoint to create users or support agents."""
    from app.core.security import hash_password
    existing = db.query(User).filter(User.email == user_in.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="User with this email already exists")

    new_user = User(
        name=user_in.name,
        email=user_in.email,
        password_hash=hash_password(user_in.password),
        role=user_in.role if user_in.role in [r.value for r in UserRole] else UserRole.CUSTOMER.value,
        account_status=AccountStatus.ACTIVE.value
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user

@router.patch("/users/{user_id}", response_model=UserResponse)
@router.put("/users/{user_id}", response_model=UserResponse)
def update_user_by_admin(
    user_id: int,
    user_update: UserUpdate,
    current_user: User = Depends(require_role([UserRole.ADMIN.value])),
    db: Session = Depends(get_db)
):
    """Update user properties (role, status, name)."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if user_update.account_status:
        val = user_update.account_status.lower()
        if val in ["disabled", "suspended", "inactive"]:
            user.account_status = AccountStatus.DISABLED.value
        elif val in ["active", "enabled"]:
            user.account_status = AccountStatus.ACTIVE.value
        else:
            raise HTTPException(status_code=400, detail="Invalid account status value")

    if user_update.role:
        if user_update.role not in [r.value for r in UserRole]:
            raise HTTPException(status_code=400, detail="Invalid role value")
        user.role = user_update.role

    if user_update.name:
        user.name = user_update.name

    if user_update.email:
        existing = db.query(User).filter(User.email == user_update.email, User.id != user_id).first()
        if existing:
            raise HTTPException(status_code=400, detail="This email is already in use by another user")
        user.email = user_update.email

    db.commit()
    db.refresh(user)
    return user

@router.delete("/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user_by_admin(
    user_id: int,
    current_user: User = Depends(require_role([UserRole.ADMIN.value])),
    db: Session = Depends(get_db)
):
    """Delete a user account (Admin only)."""
    if user_id == current_user.id:
        raise HTTPException(status_code=400, detail="Cannot delete your own admin account")
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    db.delete(user)
    db.commit()
    return None

@router.put("/users/{user_id}/status")
def toggle_user_status(
    user_id: int,
    status_value: str,
    current_user: User = Depends(require_role([UserRole.ADMIN.value])),
    db: Session = Depends(get_db)
):
    """Enable or disable user account (Query param backward compatibility)."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    val = status_value.lower()
    if val in ["disabled", "suspended", "inactive"]:
        user.account_status = AccountStatus.DISABLED.value
    elif val in ["active", "enabled"]:
        user.account_status = AccountStatus.ACTIVE.value
    else:
        raise HTTPException(status_code=400, detail="Invalid status value")
    
    db.commit()
    return {"message": f"User status updated to {user.account_status}"}
