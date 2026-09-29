# Graduation Project Presentation & Defense Guide 🎓
## AI Customer Support Platform

This document directly addresses all 16 presentation requirements specified in **Section 20** of the Graduation Project specification.

---

### Slide 1: Title & Team
- **Project Title**: AI Customer Support Platform
- **Subtitle**: Enterprise-Grade Support Automation with FastAPI, PostgreSQL, LangGraph AI Agents & n8n
- **Team Size**: 3–4 Members
- **Submission Date**: September 2026

---

### Slide 2: 1. Business Problem
- **Support Overhead**: High volume of repetitive inquiries (status requests, account questions, billing issues) saturates human support teams.
- **Delayed Response Times**: Customers experience hours or days of waiting for simple queries and escalations.
- **Inconsistent Triage**: Manual ticket priority tagging leads to missed SLA deadlines for critical outages.
- **Disconnected Tools**: Traditional chatbots operate in silos without real-time database access or tool execution.

---

### Slide 3: 2. Proposed Solution
- **Autonomous AI Agent**: An intelligent assistant integrated with the backend database via tool calling to fetch, create, and update tickets in real time.
- **LangGraph State Machine**: Deterministic, multi-node workflow orchestration rather than a simple stateless LLM wrapper.
- **AI Ticket Classification & Response Drafting**: Automatically categorizes issues upon creation and drafts human-in-the-loop responses for agents.
- **Event-Driven Automation**: n8n workflows that handle external notifications, alerting, and Google Sheets reporting.

---

### Slide 4: 3. System Architecture
- **Layer 1: Frontend SPA**: Responsive web portal with 3 dedicated dashboards (Customer, Support Agent, Admin) and an integrated floating AI chat widget.
- **Layer 2: RESTful API Gateway**: FastAPI backend enforcing JWT authentication and Role-Based Access Control (RBAC).
- **Layer 3: Agentic AI Layer**: LangGraph workflow invoking Google Gemini 2.0/2.5 Flash, equipped with 6 custom Python backend tools.
- **Layer 4: Data Layer**: PostgreSQL database managed via SQLAlchemy 2.0 ORM with relational integrity.
- **Layer 5: Business Automation**: n8n webhook listener handling alerts (Telegram/Slack), email dispatch, and Google Sheets synchronization.

---

### Slide 5: 4. Database Design
- **Users Table (`users`)**:
  - `id`, `name`, `email` (unique index), `password_hash`, `role` (Admin, Agent, Customer), `account_status` (Active, Suspended), `created_at`.
- **Tickets Table (`tickets`)**:
  - `id`, `customer_id` (FK), `assigned_agent_id` (FK, nullable), `subject`, `description`, `category`, `priority`, `status`, `ai_category`, `ai_priority`, `ai_summary`, `ai_suggested_action`, `created_at`, `updated_at`, `resolution_date`.
- **Messages Table (`messages`)**:
  - `id`, `ticket_id` (FK, cascade delete), `sender_id` (FK), `message`, `timestamp`.

---

### Slide 6: 5. Backend Architecture
- Structured according to modern FastAPI enterprise modular design:
  - `app/routers/`: Modular route definitions (`auth`, `tickets`, `messages`, `admin`, `ai`).
  - `app/services/`: Isolated business logic and asynchronous webhook dispatches (`ticket_service`, `webhook_service`).
  - `app/schemas/`: Pydantic models for validation, request parsing, and response serialization.
  - `app/core/`: Security (OAuth2 password bearer, bcrypt, JWT) and database connection pooling.

---

### Slide 7: 6. Authentication & Security
- **Algorithm**: HMAC SHA-256 (`HS256`) JWT with configurable expiration (`ACCESS_TOKEN_EXPIRE_MINUTES`).
- **Password Security**: Strong salting and hashing via `bcrypt`.
- **Role-Based Authorization (RBAC)**: Custom FastAPI dependency `require_role([...])` protecting sensitive administrative endpoints.
- **Row-Level Permission Checks**: Customers can only inspect and mutate their own support tickets.

---

### Slide 8: 7. AI Architecture Overview
- Combines foundational LLMs with agentic workflows.
- Instead of treating the LLM as a static knowledge base:
  1. The LLM acts as the **decision-making engine**.
  2. The system provides **stateful execution memory**.
  3. The LLM has direct access to **structured APIs and database tools**.

---

### Slide 9: 8. LangChain Integration
- **Chat Model**: `ChatGoogleGenerativeAI` leveraging Gemini Flash for low-latency reasoning.
- **Prompt Engineering**: Custom system prompts defining agent personas, boundaries, and formatting rules.
- **Structured Outputs**: Pydantic structured output chains for deterministic ticket classification (`ai_classify_ticket`).
- **Tool Binding**: Decorator-based LangChain `@tool` definitions providing schema and parameter documentation to the model.

---

### Slide 10: 9. LangGraph State Machine
- **StateGraph**: Tracks `MessagesState` across conversational cycles.
- **Graph Nodes**:
  - `llm`: Receives user input and bound tools, deciding whether to invoke tools or produce direct text.
  - `tools`: `ToolNode` executing selected functions with provided arguments.
  - `escalation`: Escalates tickets and informs customer of human handover.
- **Conditional Edges**: Dynamically routes from `llm -> tools` or `tools -> escalation -> END`.

---

### Slide 11: 10. Agent & Tool Calling
The agent has access to 6 core backend tools:
1. `get_customer_tickets`: Retrieves user tickets filtered by status.
2. `get_ticket_details`: Fetches full ticket details and conversation logs.
3. `create_ticket`: Creates tickets directly from conversational intent.
4. `check_ticket_status`: Quick lookup of resolution status and priority.
5. `update_ticket`: Authorized updates to priority or status.
6. `escalate_ticket`: Escalates priority to Critical and triggers urgent notifications.

---

### Slide 12: 11. n8n Automation Workflows
- **Workflow 1: New Ticket Notification**: Triggers when a ticket is created -> extracts metadata -> sends notification to support chat and customer confirmation email.
- **Workflow 2: Ticket Escalation**: Triggers when priority is set to Critical -> alerts admin team immediately via urgent email and Telegram alert.
- **Workflow 3: Google Sheets Reporting**: Triggers when a ticket is resolved -> appends ticket metrics and timestamps into a reporting spreadsheet.

---

### Slide 13: 12. Git / GitHub Team Workflow
- **Branching Strategy**: Feature-branch workflow (`feature/auth`, `feature/agent`, `feature/frontend`) merged via Pull Requests.
- **Commit Conventions**: Conventional commits (`feat:`, `fix:`, `docs:`, `test:`).
- **Code Reviews**: Peer reviews and merge validation with test pass criteria.

---

### Slide 14: 13. Live Demo Scenario
1. **Customer Login**: Sign in as John Doe (`john.customer@gmail.com`).
2. **AI Chatbot Interaction**: Ask *"Show me my open tickets"* -> Agent queries DB and lists tickets.
3. **Conversational Ticket Creation**: Tell agent *"Create a ticket: billing error on last invoice"* -> Agent creates ticket #4 with auto-classification.
4. **Escalation**: Request *"Escalate this ticket to human support immediately"* -> Agent escalates to Critical and calls n8n webhook.
5. **Agent Workspace**: Log in as Sarah Jenkins -> Review ticket, generate AI response draft, modify, and reply.
6. **Admin Dashboard**: Log in as Admin -> View real-time analytics, KPIs, and agent workload distribution.

---

### Slide 15: 14. Challenges & Engineering Solutions
- **Challenge 1: Safe Tool Execution**: Preventing unauthorized access when the LLM calls database tools.
  - *Solution*: Tools are built dynamically per session and bound to the authenticated user ID and role context.
- **Challenge 2: Multi-Turn Conversation Memory**:
  - *Solution*: Integrated LangGraph's `InMemorySaver` checkpointer keyed by `thread_id` and user ID.
- **Challenge 3: External Service Resilience**:
  - *Solution*: Asynchronous background tasks for n8n webhooks and graceful fallbacks when external APIs are unreachable.

---

### Slide 16: 15. Future Enhancements & 16. Documentation
- **Future Improvements**:
  - Retrieval-Augmented Generation (RAG) over corporate knowledge bases and manuals.
  - Real-time WebSocket streaming for agent responses.
  - Multi-agent debate or specialized sub-agents for technical vs. billing issues.
  - Deployment to AWS/GCP with Docker containers and CI/CD pipelines.
- **Documentation**:
  - Interactive OpenAPI docs at `/docs`.
  - Comprehensive `README.md` and complete test suite in `tests/test_api.py`.
