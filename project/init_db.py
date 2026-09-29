from app.core.database import engine, Base
from app.models import User, Ticket, Message

def init_database():
    print("Connecting to PostgreSQL and creating tables...")
    Base.metadata.create_all(bind=engine)
    print("Tables created successfully: users, tickets, messages!")

if __name__ == "__main__":
    init_database()
