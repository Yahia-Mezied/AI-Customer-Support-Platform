from pathlib import Path
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from app.core.config import settings
from app.routers import auth_router, tickets_router, messages_router, admin_router, ai_router

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.PROJECT_VERSION,
    description="Full-stack AI Customer Support Platform REST API with PostgreSQL, LangGraph AI Agent, and n8n Webhooks."
)

# Enable CORS for frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include Routers matching the exact project specification
app.include_router(auth_router)
app.include_router(tickets_router)
app.include_router(messages_router)
app.include_router(admin_router)
app.include_router(ai_router)

# Mount Frontend static files
BASE_DIR = Path(__file__).resolve().parent.parent
FRONTEND_DIR = BASE_DIR / "frontend"

if FRONTEND_DIR.exists():
    if (FRONTEND_DIR / "css").exists():
        app.mount("/css", StaticFiles(directory=str(FRONTEND_DIR / "css")), name="css")
    if (FRONTEND_DIR / "js").exists():
        app.mount("/js", StaticFiles(directory=str(FRONTEND_DIR / "js")), name="js")
    app.mount("/static", StaticFiles(directory=str(FRONTEND_DIR)), name="static")

@app.get("/health", tags=["Health"])
def health():
    return {
        "status": "online",
        "project": settings.PROJECT_NAME,
        "docs_url": "/docs",
        "version": settings.PROJECT_VERSION
    }

@app.get("/", tags=["Health"])
def root(request: Request):
    accept = request.headers.get("accept", "")
    # If request comes from a browser, serve the frontend app
    if "text/html" in accept and FRONTEND_DIR.exists() and (FRONTEND_DIR / "index.html").exists():
        return FileResponse(str(FRONTEND_DIR / "index.html"))
    
    # Otherwise return JSON health check for test runners & API clients
    return {
        "status": "online",
        "project": settings.PROJECT_NAME,
        "docs_url": "/docs",
        "version": settings.PROJECT_VERSION
    }

