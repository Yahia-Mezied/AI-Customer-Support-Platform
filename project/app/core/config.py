import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    PROJECT_NAME: str = "AI Customer Support Platform"
    PROJECT_VERSION: str = "1.0.0"
    
    # Database
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL", 
        "postgresql+psycopg2://postgres:2004@localhost:5432/ai_support_db"
    )
    
    # JWT
    SECRET_KEY: str = os.getenv("SECRET_KEY", "supersecretjwtkeyforaisupportplatform2026project")
    ALGORITHM: str = os.getenv("ALGORITHM", "HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "1440"))
    
    # n8n Webhook URLs (Supports both naming conventions)
    N8N_WEBHOOK_TICKET_CREATED: str = (
        os.getenv("N8N_NEW_TICKET_WEBHOOK") or
        os.getenv("N8N_WEBHOOK_TICKET_CREATED") or
        "http://localhost:5678/webhook/ticket-created"
    )
    N8N_WEBHOOK_TICKET_ESCALATED: str = (
        os.getenv("N8N_ESCALATION_WEBHOOK") or
        os.getenv("N8N_WEBHOOK_TICKET_ESCALATED") or
        "http://localhost:5678/webhook/ticket-escalated"
    )
    N8N_WEBHOOK_TICKET_RESOLVED: str = (
        os.getenv("N8N_REPORT_WEBHOOK") or
        os.getenv("N8N_WEBHOOK_TICKET_RESOLVED") or
        "http://localhost:5678/webhook/ticket-resolved"
    )
    
    # AI / LLM Configuration
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY", "")
    GEMINI_MODEL: str = os.getenv("GEMINI_MODEL", "gemini-3.5-flash") 
    BACKEND_URL: str = os.getenv("BACKEND_URL", "http://localhost:8000")

settings = Settings()
