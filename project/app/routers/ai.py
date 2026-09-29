import logging
from typing import Dict, Any, Optional, Literal
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from langchain_core.messages import HumanMessage
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User, UserRole
from app.agent.graph import build_graph, get_llm
from app.agent.prompts import SUGGEST_RESPONSE_PROMPT, CLASSIFY_PROMPT

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/ai", tags=["AI Agent (LangChain & LangGraph)"])

# --- Request / Response Schemas ---

class ChatRequest(BaseModel):
    message: str = Field(..., description="Message from customer to AI Assistant")
    thread_id: Optional[str] = Field("default", description="Conversation thread identifier for memory")

class ChatResponse(BaseModel):
    reply: str
    user_id: int
    user_name: str
    thread_id: str

class SuggestResponseRequest(BaseModel):
    ticket_id: int
    customer_message: Optional[str] = None

class SuggestResponseResponse(BaseModel):
    ticket_id: int
    suggested_response: str

class ClassifyTicketRequest(BaseModel):
    subject: Optional[str] = None
    description: Optional[str] = None
    text: Optional[str] = None

class ClassifyTicketResponse(BaseModel):
    category: Literal["Technical Issue", "Account Issue", "Billing", "Product Issue", "General Inquiry"] = "General Inquiry"
    priority: Literal["Low", "Medium", "High", "Critical"] = "Medium"
    summary: str
    suggested_action: str


# --- Endpoints ---

@router.post("/chat", response_model=ChatResponse)
async def ai_chat(
    req: ChatRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """AI Agent conversational endpoint powered by LangGraph state machine.
    Processes user queries, dynamically calls tools when needed, and escalates when appropriate.
    """
    try:
        graph = build_graph(current_user=current_user)
        thread_key = f"{current_user.id}:{req.thread_id or 'default'}"
        config = {"configurable": {"thread_id": thread_key}}

        result = await graph.ainvoke(
            {"messages": [HumanMessage(content=req.message)]},
            config=config
        )

        messages = result.get("messages", [])
        if messages:
            last_message = messages[-1]
            raw_content = last_message.content if hasattr(last_message, "content") else str(last_message)
            if isinstance(raw_content, list):
                parts = []
                for p in raw_content:
                    if isinstance(p, dict) and "text" in p:
                        parts.append(p["text"])
                    elif isinstance(p, str):
                        parts.append(p)
                    else:
                        parts.append(str(p))
                reply_text = "\n".join(parts)
            else:
                reply_text = str(raw_content)
        else:
            reply_text = "I received your message, but no response was generated."

        return ChatResponse(
            reply=reply_text,
            user_id=current_user.id,
            user_name=current_user.name,
            thread_id=req.thread_id or "default"
        )
    except Exception as e:
        logger.error(f"Error in ai_chat: {e}", exc_info=True)
        return ChatResponse(
            reply=f"AI Agent encountered a temporary issue: {str(e)}",
            user_id=current_user.id,
            user_name=current_user.name,
            thread_id=req.thread_id or "default"
        )


@router.post("/suggest-response", response_model=SuggestResponseResponse)
async def ai_suggest_response(
    req: SuggestResponseRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Suggest professional response for support agent to review, edit, and send."""
    from app.services import ticket_service
    customer_msg = req.customer_message
    if not customer_msg:
        # Fetch last message or description
        ticket = ticket_service.get_ticket_by_id(db, req.ticket_id)
        messages = ticket_service.get_ticket_messages(db, req.ticket_id) if ticket else []
        if messages:
            customer_msg = messages[-1].message
        elif ticket:
            customer_msg = ticket.description
        else:
            customer_msg = "Please help me resolve this issue."

    llm = get_llm()
    if llm is None:
        fallback = (
            f"Dear customer,\n\n"
            f"Thank you for contacting our support team regarding ticket #{req.ticket_id}. "
            f"We are actively reviewing your case: '{customer_msg[:80]}...' "
            f"and will provide you with a resolution as soon as possible.\n\n"
            f"Best regards,\n{current_user.name} - Support Team"
        )
        return SuggestResponseResponse(
            ticket_id=req.ticket_id,
            suggested_response=fallback
        )

    try:
        prompt = ChatPromptTemplate.from_messages([
            ("system", SUGGEST_RESPONSE_PROMPT),
            ("human", "Ticket #{ticket_id}\nCustomer message:\n{customer_message}")
        ])
        chain = prompt | llm | StrOutputParser()
        suggestion = await chain.ainvoke({
            "ticket_id": req.ticket_id,
            "customer_message": customer_msg
        })
        return SuggestResponseResponse(
            ticket_id=req.ticket_id,
            suggested_response=suggestion
        )
    except Exception as e:
        logger.error(f"Error in ai_suggest_response: {e}")
        return SuggestResponseResponse(
            ticket_id=req.ticket_id,
            suggested_response=f"Thank you for reaching out regarding ticket #{req.ticket_id}. We are investigating your inquiry."
        )


@router.post("/classify-ticket", response_model=ClassifyTicketResponse)
async def ai_classify_ticket(
    req: ClassifyTicketRequest,
    db: Session = Depends(get_db)
):
    """Auto-classify ticket category, priority, summary, and suggested action using LLM."""
    subject = req.subject or (req.text[:50] if req.text else "Support Inquiry")
    description = req.description or (req.text if req.text else "")

    llm = get_llm()
    if llm is None:
        # Heuristic classification fallback when API key is missing
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

        return ClassifyTicketResponse(
            category=cat,
            priority=prio,
            summary=(description[:100] if description else subject),
            suggested_action=f"Assign to {cat} specialist for investigation."
        )

    try:
        prompt = ChatPromptTemplate.from_messages([
            ("system", CLASSIFY_PROMPT),
            ("human", "Subject: {subject}\nDescription: {description}")
        ])
        structured_llm = llm.with_structured_output(ClassifyTicketResponse)
        chain = prompt | structured_llm
        result = await chain.ainvoke({
            "subject": subject,
            "description": description
        })
        return result
    except Exception as e:
        logger.error(f"Error in ai_classify_ticket: {e}")
        return ClassifyTicketResponse(
            category="General Inquiry",
            priority="Medium",
            summary=description[:100] if description else subject,
            suggested_action="Review customer details and verify request."
        )
