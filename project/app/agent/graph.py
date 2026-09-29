"""LangGraph Agent workflow implementation for AI Customer Support.

Implements the multi-node workflow specified in Sections 10 & 11:
- Node 1: Receive Message (User message input)
- Node 2: Analyze Request & Decide (LLM call with bound tools)
- Node 3: Execute Tools (ToolNode)
- Node 4: Escalation (Handles escalated tickets)
- Node 5: Return / Stream Response
"""

import os
import logging
from typing import Dict, Any, Optional
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from langgraph.graph import StateGraph, MessagesState, START, END
from langgraph.prebuilt import ToolNode
from langgraph.checkpoint.memory import InMemorySaver

from app.core.config import settings
from app.models.user import User
from app.agent.tools import build_tools
from app.agent.prompts import SUPPORT_SYSTEM_PROMPT

logger = logging.getLogger(__name__)

# In-memory checkpointer for multi-turn conversation memory
checkpointer = InMemorySaver()

def get_llm():
    """Retrieve ChatGoogleGenerativeAI instance using configured API key."""
    api_key = settings.GEMINI_API_KEY or os.getenv("GOOGLE_API_KEY")
    if not api_key:
        return None
    return ChatGoogleGenerativeAI(
        model=getattr(settings, "GEMINI_MODEL", "gemini-2.5-flash"),
        temperature=0.1,
        api_key=api_key
    )


def build_graph(current_user: User):
    """Build and compile the LangGraph workflow tailored for the current user."""
    tools = build_tools(current_user)
    llm = get_llm()

    system_prompt = (
        f"{SUPPORT_SYSTEM_PROMPT}\n\n"
        f"Current User Context:\n"
        f"- ID: {current_user.id}\n"
        f"- Name: {current_user.name}\n"
        f"- Role: {current_user.role}\n"
    )
    system_msg = SystemMessage(content=system_prompt)

    if llm is None:
        # Fallback graph when Gemini API Key is not yet configured
        def mock_llm_node(state: MessagesState):
            last_msg = state["messages"][-1].content if state["messages"] else ""
            reply = (
                f"[AI Demo Mode] Hello {current_user.name}! I received: '{last_msg}'. "
                f"To enable live Gemini 2.0 Flash reasoning, please set GEMINI_API_KEY in your .env file."
            )
            return {"messages": [AIMessage(content=reply)]}

        builder = StateGraph(MessagesState)
        builder.add_node("llm", mock_llm_node)
        builder.add_edge(START, "llm")
        builder.add_edge("llm", END)
        return builder.compile(checkpointer=checkpointer)

    llm_with_tools = llm.bind_tools(tools)

    def call_llm(state: MessagesState):
        messages = [system_msg] + state["messages"]
        response = llm_with_tools.invoke(messages)
        return {"messages": [response]}

    def escalation_node(state: MessagesState):
        """Escalation handler node when human intervention is triggered."""
        notice = AIMessage(
            content="Your issue has been escalated to our human support team with Critical priority. "
                    "A human specialist is reviewing your case and will follow up shortly."
        )
        return {"messages": [notice]}

    def route_from_llm(state: MessagesState):
        """Route to tools if the LLM made any tool calls, otherwise finish."""
        last_message = state["messages"][-1]
        if hasattr(last_message, "tool_calls") and last_message.tool_calls:
            return "tools"
        return END

    def route_after_tools(state: MessagesState):
        """Check if escalation tool was executed, otherwise return to LLM to summarize results."""
        for msg in reversed(state["messages"]):
            if hasattr(msg, "name") and msg.name == "escalate_ticket":
                return "escalation"
        return "llm"

    tool_node = ToolNode(tools)

    builder = StateGraph(MessagesState)
    builder.add_node("llm", call_llm)
    builder.add_node("tools", tool_node)
    builder.add_node("escalation", escalation_node)

    builder.add_edge(START, "llm")

    builder.add_conditional_edges("llm", route_from_llm, {
        "tools": "tools",
        END: END
    })

    builder.add_conditional_edges("tools", route_after_tools, {
        "escalation": "escalation",
        "llm": "llm"
    })

    builder.add_edge("escalation", END)

    return builder.compile(checkpointer=checkpointer)
