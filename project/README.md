# AI Customer Support Platform 🤖🎫

A production-grade, full-stack customer support management platform featuring an autonomous **LangGraph AI Agent**, **FastAPI** REST backend, **PostgreSQL** persistence, **n8n** workflow automation, and a modern web interface.

Built as a Graduation Project adhering to the official project specifications.

---

## 📌 Table of Contents
- [Architecture & Tech Stack](#-architecture--tech-stack)
- [Key Features & Capabilities](#-key-features--capabilities)
- [Project Structure](#-project-structure)
- [Getting Started](#-getting-started)
  - [Prerequisites](#prerequisites)
  - [Environment Configuration](#environment-configuration)
  - [Database Setup & Seeding](#database-setup--seeding)
  - [Running the Application](#running-the-application)
- [Default Demo Accounts](#-default-demo-accounts)
- [API Endpoints Overview](#-api-endpoints-overview)
- [AI Agent & LangGraph Architecture](#-ai-agent--langgraph-architecture)
- [n8n Automation Workflows](#-n8n-automation-workflows)
- [Testing & Verification](#-testing--verification)
- [Final Presentation & Live Demo Guide](#-final-presentation--live-demo-guide)

---

## 🏗️ Architecture & Tech Stack

```mermaid
graph TD
    Client[Web Frontend: Customer / Agent / Admin] -->|REST API & JWT| FastAPI[FastAPI Backend]
    FastAPI -->|ORM / SQL| DB[(PostgreSQL Database)]
    FastAPI -->|Graph State Machine| LangGraph[LangGraph AI Agent]
    LangGraph -->|Tool Calling| BackendTools[Backend Database & Business Tools]
    LangGraph -->|LLM Reasoning| Gemini[Google Gemini 2.0/2.5 Flash]
    FastAPI -->|Async Webhooks| n8n[n8n Workflow Automation]
    n8n -->|Alerts| Telegram[Telegram / Slack Alerts]
    n8n -->|Emails| Email[Automated Email Notification]
    n8n -->|Append Row| Sheets[Google Sheets Reporting]
```

- **Backend Framework**: [FastAPI](https://fastapi.tiangolo.com/) (Python 3.10+)
- **Database & ORM**: PostgreSQL via [SQLAlchemy 2.0](https://www.sqlalchemy.org/)
- **AI Agent Framework**: [LangChain](https://www.langchain.com/) & [LangGraph](https://langchain-ai.github.io/langgraph/)
- **LLM Engine**: Google Gemini Flash via `langchain-google-genai`
- **Workflow Automation**: [n8n](https://n8n.io/)
- **Authentication**: JWT (JSON Web Tokens) with `bcrypt` password hashing
- **Frontend**: Responsive Single-Page Application (HTML5, Vanilla CSS, JavaScript, TailwindCSS CDN)

---

## 🚀 Key Features & Capabilities

### 1. Role-Based Access Control (RBAC)
- **Customer**: Submit tickets, filter personal tickets, live AI chatbot assistant, reply in conversation threads.
- **Support Agent**: View assigned tickets, update ticket statuses, reassign tickets, human-in-the-loop AI response drafting.
- **Admin**: Full platform analytics & KPIs, user management, account activation/suspension, agent allocation.

### 2. Autonomous LangGraph AI Agent
- **Dynamic Tool Calling**: Determines whether to answer directly or query backend tools.
- **6 Backend Tools**:
  1. `get_customer_tickets`: Fetch customer tickets filtered by status.
  2. `get_ticket_details`: Retrieve details and conversation history.
  3. `create_ticket`: Create a ticket with category & priority.
  4. `check_ticket_status`: Check real-time progress.
  5. `update_ticket`: Modify allowed ticket attributes.
  6. `escalate_ticket`: Escalate priority to Critical and alert human agents.
- **AI Ticket Classification**: Auto-extracts category, priority, short summary, and suggested next steps upon ticket creation.
- **AI Response Suggestions**: Empowers support agents to generate, review, and edit professional replies before sending.

### 3. Business Automation via n8n
- **Workflow 1 (New Ticket Notification)**: Triggers on new ticket creation, parses data, and notifies the support channel and customer.
- **Workflow 2 (Ticket Escalation)**: Triggers when priority escalates to Critical, alerting administrators immediately via email and Telegram.
- **Workflow 3 (Google Sheets Reporting)**: Appends resolved ticket details to Google Sheets for business reporting and SLA audits.

---

## 📁 Project Structure

```
project1/
├── app/
│   ├── main.py                     # FastAPI entry point & static file routing
│   ├── core/
│   │   ├── config.py               # Environment configuration settings
│   │   ├── database.py             # SQLAlchemy session & DB engine
│   │   └── security.py             # JWT handling & password hashing
│   ├── models/
│   │   ├── user.py                 # User table model (Customer, Agent, Admin)
│   │   ├── ticket.py               # Ticket table model with AI metadata
│   │   └── message.py              # Ticket conversation message model
│   ├── schemas/
│   │   ├── user.py                 # User Pydantic schemas
│   │   └── ticket.py               # Ticket & Message Pydantic schemas
│   ├── services/
│   │   ├── ticket_service.py       # Ticket business logic & classification
│   │   └── webhook_service.py      # Async webhook dispatcher to n8n
│   ├── agent/
│   │   ├── prompts.py              # System prompts for agent & suggestions
│   │   ├── tools.py                # 6 LangChain tools bound to user context
│   │   └── graph.py                # LangGraph state machine & nodes
│   └── routers/
│       ├── auth.py                 # /auth endpoints (register, login, me)
│       ├── tickets.py              # /tickets endpoints (CRUD, escalate)
│       ├── messages.py             # /tickets/{id}/messages
│       ├── admin.py                # /admin endpoints (stats, users, agents)
│       └── ai.py                   # /ai endpoints (chat, classify, suggest)
├── frontend/
│   ├── index.html                  # Single page portal UI
│   ├── css/styles.css              # Custom styling & glassmorphism theme
│   └── js/
│       ├── config.js               # API endpoints & utility functions
│       ├── auth.js                 # Authentication & navigation router
│       ├── customer.js             # Customer dashboard, tickets & chat widget
│       ├── agent.js                # Support agent workspace
│       └── admin.js                # Admin KPIs & user management
├── n8n_workflows/
│   ├── workflow_1_ticket_created.json
│   ├── workflow_2_ticket_escalated.json
│   └── workflow_3_google_sheets_reporting.json
├── tests/
│   └── test_api.py                 # Automated end-to-end integration tests
├── .env.example                    # Sample environment variables
├── requirements.txt                # Python dependencies
├── init_db.py                      # Database schema initialiser
└── seed_data.py                    # Initial demo dataset seeder
```

---

## ⚙️ Getting Started

### Prerequisites
- Python 3.10 or higher
- PostgreSQL (14+) installed and running locally
- (Optional) n8n running on port 5678 (via Docker or `npx n8n`)

### Environment Configuration
Copy the `.env.example` file to `.env`:
```bash
cp .env.example .env
```
Edit `.env` with your PostgreSQL credentials and Gemini API key:
```ini
DATABASE_URL=postgresql+psycopg2://postgres:YOUR_PASSWORD@localhost:5432/ai_support_db
SECRET_KEY=supersecretjwtkeyforaisupportplatform2026project
GEMINI_API_KEY=YOUR_GEMINI_API_KEY
```

### Database Setup & Seeding
1. Create the database in PostgreSQL:
   ```sql
   CREATE DATABASE ai_support_db;
   ```
2. Initialize the tables and schema:
   ```bash
   python init_db.py
   ```
3. Populate with initial demo users, tickets, and conversations:
   ```bash
   python seed_data.py
   ```

### Running the Application
Launch the FastAPI server with hot-reload:
```bash
uvicorn app.main:app --reload --port 8000
```
- **Web App**: Open [http://localhost:8000](http://localhost:8000) in your browser.
- **Interactive API Docs (Swagger UI)**: Open [http://localhost:8000/docs](http://localhost:8000/docs).

---

## 👥 Default Demo Accounts

After running `seed_data.py`, use any of these pre-configured accounts:

| Role | Email | Password | Access Capabilities |
| :--- | :--- | :--- | :--- |
| **Admin** | `admin@support.com` | `admin123` | Full Dashboard, KPIs, Manage Users/Agents |
| **Support Agent** | `sarah.agent@support.com` | `agent123` | Workspace, Ticket Statuses, AI Response Drafting |
| **Support Agent** | `david.agent@support.com` | `agent123` | Workspace, Ticket Statuses, Reassignment |
| **Customer** | `john.customer@gmail.com` | `customer123` | Create Tickets, View My Tickets, AI Assistant Chatbot |
| **Customer** | `alice.customer@yahoo.com` | `customer123` | Create Tickets, View My Tickets, AI Assistant Chatbot |

---

## 📡 API Endpoints Overview

### Authentication (`/auth`)
- `POST /auth/register`: Create a new customer account.
- `POST /auth/login`: Authenticate and obtain JWT access token.
- `GET /auth/me`: Get current authenticated user profile.

### Ticket Management (`/tickets`)
- `GET /tickets`: List accessible tickets (filtered by role and optional status/priority).
- `POST /tickets`: Create a ticket (triggers AI auto-classification and n8n webhook).
- `GET /tickets/{id}`: Retrieve detailed ticket view.
- `PUT /tickets/{id}`: Update ticket status, priority, or assigned agent.
- `POST /tickets/{id}/escalate`: Explicitly escalate ticket to Critical priority.
- `DELETE /tickets/{id}`: Delete ticket (Admin only).

### Ticket Conversation (`/tickets/{id}/messages`)
- `GET /tickets/{id}/messages`: Fetch conversation history.
- `POST /tickets/{id}/messages`: Add user or agent message to thread.

### AI & LangGraph (`/ai`)
- `POST /ai/chat`: Interactive chat with autonomous LangGraph Agent.
- `POST /ai/classify-ticket`: Run LLM classification (Category, Priority, Summary, Action).
- `POST /ai/suggest-response`: Generate suggested reply for support agents (human-in-the-loop).

### Admin & Analytics (`/admin`)
- `GET /admin/stats`: Aggregate KPIs, status distribution, and agent workloads.
- `GET /admin/users`: List system users.
- `POST /admin/users`: Create support agents or customer accounts.
- `PATCH /admin/users/{id}`: Update user role or account status (Active/Suspended).

---

## 🧠 AI Agent & LangGraph Architecture

The system utilizes **LangGraph** to model the AI Agent as a stateful computational graph:

```
[START]
   │
   ▼
[Node: LLM Reasoning & Intent Analysis]
   │
   ├─► Tool Call Required? ──► [Node: ToolNode Execution]
   │                                  │
   │                                  ▼
   │                            [Escalation Triggered?]
   │                              ├─► Yes ──► [Node: Escalation Handler] ──► [END]
   │                              └─► No  ──► Back to [LLM Reasoning]
   │
   └─► Direct Response ──► [END]
```

- **LangChain Core**: Structured prompts, message state types (`HumanMessage`, `AIMessage`, `SystemMessage`), and tool binding via `.bind_tools()`.
- **LangGraph Checkpointer**: Maintains contextual conversation history across multi-turn user dialogs.
- **Fail-safe Mode**: If no Gemini API key is configured, the agent runs in graceful demo mode without crashing.

---

## 🔄 n8n Automation Workflows

Import the JSON workflow definitions from `n8n_workflows/` into your n8n instance:

1. **`workflow_1_ticket_created.json`**:
   - Webhook trigger on `/webhook/ticket-created`
   - Parses ticket ID, customer info, subject, and AI classification
   - Dispatches Slack/Telegram message to support team and sends email acknowledgment to customer.
2. **`workflow_2_ticket_escalated.json`**:
   - Webhook trigger on `/webhook/ticket-escalated`
   - Evaluates if priority equals `Critical`
   - Dispatches urgent alert emails and notifications to team leads.
3. **`workflow_3_google_sheets_reporting.json`**:
   - Webhook trigger on `/webhook/ticket-resolved`
   - Formats ticket resolution metrics and appends a row to a centralized Google Sheet.

---

## 🧪 Testing & Verification

Run the comprehensive integration test suite verifying all 12 core functional flows:

```bash
python tests/test_api.py
```

Expected output:
```
Connecting to FastAPI in-process test client...
All 12 Core Endpoints and Workflows Verified Successfully! 100% Operational.
```

---

## 🎯 Final Presentation & Live Demo Guide

To demonstrate the full end-to-end scenario during project defense:

1. **Step 1: Customer Ticket & AI Classification**
   - Log in as `john.customer@gmail.com`.
   - Create a ticket: *"I was charged twice on my credit card for invoice #904."*
   - Observe automatic AI classification (`Billing`, `High/Critical` priority).
2. **Step 2: AI Conversational Agent**
   - Open the floating chatbot widget at the bottom right.
   - Ask: *"What is the status of my open tickets?"*
   - Observe the agent invoking `get_customer_tickets` tool and returning live database results.
3. **Step 3: Escalation Workflow**
   - In chat, say: *"I need this escalated to a manager immediately."*
   - Observe the agent executing `escalate_ticket`, raising priority to Critical, and dispatching an n8n webhook notification.
4. **Step 4: Support Agent & AI Response Suggestion**
   - Log out and log in as `sarah.agent@support.com`.
   - Open the newly escalated ticket.
   - Click **"✨ Suggest AI response"** to generate a draft. Edit and send the response.
5. **Step 5: Admin Analytics & Workload**
   - Log out and log in as `admin@support.com`.
   - Review live KPIs, category distribution charts, and agent workload balances.
