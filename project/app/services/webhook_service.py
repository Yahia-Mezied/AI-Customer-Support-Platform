import httpx
import logging
from typing import Dict, Any
from app.core.config import settings

logger = logging.getLogger(__name__)

async def trigger_n8n_webhook(webhook_url: str, payload: Dict[str, Any]) -> bool:
    """Send an async event notification to an n8n webhook."""
    if not webhook_url:
        return False
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.post(webhook_url, json=payload)
            if response.status_code < 400:
                logger.info(f"Successfully triggered n8n webhook {webhook_url}")
                return True
            else:
                logger.warning(f"n8n webhook responded with status {response.status_code}")
                return False
    except Exception as e:
        logger.warning(f"Could not connect to n8n webhook ({webhook_url}): {e}")
        return False

async def notify_ticket_created(ticket_data: Dict[str, Any]):
    return await trigger_n8n_webhook(settings.N8N_WEBHOOK_TICKET_CREATED, ticket_data)

async def notify_ticket_escalated(ticket_data: Dict[str, Any]):
    return await trigger_n8n_webhook(settings.N8N_WEBHOOK_TICKET_ESCALATED, ticket_data)

async def notify_ticket_resolved(ticket_data: Dict[str, Any]):
    return await trigger_n8n_webhook(settings.N8N_WEBHOOK_TICKET_RESOLVED, ticket_data)
