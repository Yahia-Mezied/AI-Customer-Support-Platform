from datetime import datetime, timezone
from app.core.database import SessionLocal, Base, engine
from app.core.security import hash_password
from app.models.user import User, UserRole, AccountStatus
from app.models.ticket import Ticket, TicketCategory, TicketPriority, TicketStatus
from app.models.message import Message

def seed_database():
    db = SessionLocal()
    try:
        # Check if users already exist
        if db.query(User).first():
            print("Database already contains data. Skipping seeding.")
            return

        print("Seeding initial users...")
        # 1. Admin
        admin = User(
            name="System Admin",
            email="admin@support.com",
            password_hash=hash_password("admin123"),
            role=UserRole.ADMIN.value,
            account_status=AccountStatus.ACTIVE.value
        )
        # 2. Agents
        agent1 = User(
            name="Sarah Jenkins (Support Lead)",
            email="sarah.agent@support.com",
            password_hash=hash_password("agent123"),
            role=UserRole.AGENT.value,
            account_status=AccountStatus.ACTIVE.value
        )
        agent2 = User(
            name="David Miller (Tech Specialist)",
            email="david.agent@support.com",
            password_hash=hash_password("agent123"),
            role=UserRole.AGENT.value,
            account_status=AccountStatus.ACTIVE.value
        )
        # 3. Customers
        customer1 = User(
            name="John Doe",
            email="john.customer@gmail.com",
            password_hash=hash_password("customer123"),
            role=UserRole.CUSTOMER.value,
            account_status=AccountStatus.ACTIVE.value
        )
        customer2 = User(
            name="Alice Smith",
            email="alice.customer@yahoo.com",
            password_hash=hash_password("customer123"),
            role=UserRole.CUSTOMER.value,
            account_status=AccountStatus.ACTIVE.value
        )

        db.add_all([admin, agent1, agent2, customer1, customer2])
        db.commit()
        db.refresh(customer1)
        db.refresh(customer2)
        db.refresh(agent1)

        print("Seeding sample tickets...")
        t1 = Ticket(
            customer_id=customer1.id,
            assigned_agent_id=agent1.id,
            subject="Cannot log in after resetting password",
            description="I recently updated my password, but now the system displays invalid credentials error.",
            category=TicketCategory.ACCOUNT.value,
            priority=TicketPriority.HIGH.value,
            status=TicketStatus.IN_PROGRESS.value,
            ai_category="Account Issue",
            ai_priority="High",
            ai_summary="User unable to authenticate following password update.",
            ai_suggested_action="Reset authentication tokens and verify user status in active directory."
        )

        t2 = Ticket(
            customer_id=customer2.id,
            assigned_agent_id=None,
            subject="Double charge on subscription renewal",
            description="My credit card was charged twice for the September pro plan subscription.",
            category=TicketCategory.BILLING.value,
            priority=TicketPriority.CRITICAL.value,
            status=TicketStatus.OPEN.value,
            ai_category="Billing",
            ai_priority="Critical",
            ai_summary="Duplicate payment transaction detected for pro subscription.",
            ai_suggested_action="Issue immediate refund for the secondary transaction reference."
        )

        t3 = Ticket(
            customer_id=customer1.id,
            assigned_agent_id=agent1.id,
            subject="How to export tickets report?",
            description="I need to know if there is an export button for previous ticket logs.",
            category=TicketCategory.GENERAL.value,
            priority=TicketPriority.LOW.value,
            status=TicketStatus.RESOLVED.value,
            resolution_date=datetime.now(timezone.utc),
            ai_category="General Inquiry",
            ai_priority="Low",
            ai_summary="Customer inquiring about ticket reporting capabilities.",
            ai_suggested_action="Direct customer to the export tab in user settings."
        )

        db.add_all([t1, t2, t3])
        db.commit()
        db.refresh(t1)

        print("Seeding sample conversation messages...")
        m1 = Message(
            ticket_id=t1.id,
            sender_id=customer1.id,
            message="Hello, I still cannot access my account even after clearing browser cookies."
        )
        m2 = Message(
            ticket_id=t1.id,
            sender_id=agent1.id,
            message="Hi John, we have identified a sync delay with the auth server. Please try logging in now."
        )
        db.add_all([m1, m2])
        db.commit()

        print("Seeding completed successfully!")
        print("\nTest Accounts Available:")
        print("  Admin:    admin@support.com        / admin123")
        print("  Agent 1:  sarah.agent@support.com  / agent123")
        print("  Agent 2:  david.agent@support.com  / agent123")
        print("  Customer: john.customer@gmail.com  / customer123")
        print("  Customer: alice.customer@yahoo.com / customer123")

    finally:
        db.close()

if __name__ == "__main__":
    seed_database()
