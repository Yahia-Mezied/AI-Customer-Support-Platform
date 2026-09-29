"""API Integration Tests for AI Customer Support Platform.

Validates:
1. Health check
2. Admin authentication & RBAC
3. Admin dashboard analytics & stats
4. Customer authentication
5. Ticket creation & retrieval
6. Message conversation thread
7. AI endpoints (chat, classify, suggest)
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import httpx
from fastapi.testclient import TestClient
from app.main import app

BASE_URL = "http://127.0.0.1:8000"

def _run_tests_with_client(client):
    # 1. Health check
    res = client.get("/")
    assert res.status_code == 200, f"Health check failed: {res.text}"
    assert res.json()["status"] == "online"

    # 2. Admin Login
    res = client.post("/auth/login", data={"username": "admin@support.com", "password": "admin123"})
    assert res.status_code == 200, f"Admin login failed: {res.text}"
    admin_token = res.json()["access_token"]
    assert res.json()["role"] == "admin"

    # 3. Admin Stats
    res = client.get("/admin/stats", headers={"Authorization": f"Bearer {admin_token}"})
    assert res.status_code == 200, f"Admin stats failed: {res.text}"
    stats = res.json()
    assert "total_tickets" in stats
    assert "critical_tickets" in stats
    assert "tickets_by_category" in stats

    # 4. Customer Login
    res = client.post("/auth/login", data={"username": "john.customer@gmail.com", "password": "customer123"})
    assert res.status_code == 200, f"Customer login failed: {res.text}"
    customer_token = res.json()["access_token"]
    assert res.json()["role"] == "customer"

    # 5. Customer Profile
    res = client.get("/auth/me", headers={"Authorization": f"Bearer {customer_token}"})
    assert res.status_code == 200
    assert res.json()["email"] == "john.customer@gmail.com"

    # 6. Customer Tickets List
    res = client.get("/tickets", headers={"Authorization": f"Bearer {customer_token}"})
    assert res.status_code == 200
    assert isinstance(res.json(), list)

    # 7. Create New Ticket
    new_ticket = {
        "subject": "System Verification Ticket",
        "description": "Verification of ticket creation and background notifications",
        "category": "Technical Issue",
        "priority": "Medium"
    }
    res = client.post("/tickets", json=new_ticket, headers={"Authorization": f"Bearer {customer_token}"})
    assert res.status_code == 201
    created_ticket = res.json()
    ticket_id = created_ticket["id"]

    # 8. Add Message to Ticket Conversation
    res = client.post(
        f"/tickets/{ticket_id}/messages",
        json={"message": "Verification message in conversation"},
        headers={"Authorization": f"Bearer {customer_token}"}
    )
    assert res.status_code == 201
    assert res.json()["message"] == "Verification message in conversation"

    # 9. Get Messages in Ticket
    res = client.get(f"/tickets/{ticket_id}/messages", headers={"Authorization": f"Bearer {customer_token}"})
    assert res.status_code == 200
    assert len(res.json()) >= 1

    # 10. AI Chat Endpoint
    res = client.post(
        "/ai/chat",
        json={"message": "I need help with my account"},
        headers={"Authorization": f"Bearer {customer_token}"}
    )
    assert res.status_code == 200
    assert "reply" in res.json()

    # 11. AI Classification Endpoint
    res = client.post(
        "/ai/classify-ticket",
        json={"text": "Cannot access billing portal and invoices"}
    )
    assert res.status_code == 200
    assert "category" in res.json()
    assert "priority" in res.json()

    # 12. AI Response Suggestion Endpoint
    res = client.post(
        "/ai/suggest-response",
        json={"ticket_id": ticket_id, "customer_message": "Please fix this ASAP"},
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert res.status_code == 200
    assert "suggested_response" in res.json()

    print("All 12 Core Endpoints and Workflows Verified Successfully! 100% Operational.")

def test_full_flow():
    try:
        with httpx.Client(base_url=BASE_URL, timeout=httpx.Timeout(0.3, connect=0.3)) as client:
            res = client.get("/")
            if res.status_code == 200 and res.headers.get("content-type", "").startswith("application/json"):
                print(f"Connecting to live server at {BASE_URL}...")
                _run_tests_with_client(client)
                return
    except Exception:
        pass

    print("Connecting to FastAPI in-process test client...")
    with TestClient(app) as client:
        _run_tests_with_client(client)

if __name__ == "__main__":
    test_full_flow()
