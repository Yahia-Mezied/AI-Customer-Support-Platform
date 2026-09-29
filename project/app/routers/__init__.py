from app.routers.auth import router as auth_router
from app.routers.tickets import router as tickets_router
from app.routers.messages import router as messages_router
from app.routers.admin import router as admin_router
from app.routers.ai import router as ai_router

__all__ = [
    "auth_router",
    "tickets_router",
    "messages_router",
    "admin_router",
    "ai_router"
]
