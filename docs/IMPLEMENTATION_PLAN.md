# Implementation Plan: Conversational Mortgage Assistant

## Tech Stack (Agreed)
- **Frontend**: Next.js 14+ (App Router) → Deploy on Vercel
- **Backend**: FastAPI (Python) → Deploy on Railway
- **AI**: Groq Python SDK (direct, no LangChain)
- **State**: In-memory (Python dict)
- **Leads**: JSON file storage
- **Development**: Docker Desktop for local testing

---

## Phase 1: Backend Foundation (Core Logic)

### Step 1.1: Project Structure
```
mortgage-assistant/
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py          # FastAPI app
│   │   ├── agent.py         # Groq SDK agent with function calling
│   │   ├── tools.py          # Math functions (EMI, LTV, etc.)
│   │   ├── state.py          # In-memory conversation state
│   │   └── models.py         # Pydantic models
│   ├── Dockerfile            # Docker image for backend
│   ├── requirements.txt
│   ├── .env.example
│   └── .env                  # Local dev (gitignored)
├── frontend/
│   ├── app/
│   │   ├── page.tsx         # Main chat page
│   │   └── api/             # Next.js API routes (if needed)
│   ├── components/
│   │   ├── Chat.tsx          # Chat UI component
│   │   └── LeadCapture.tsx  # Lead form
│   └── package.json
└── docker-compose.yml         # Local development setup
```

### Step 1.2: Math Functions (tools.py)
**Purpose**: Pure Python functions for calculations (no LLM math)

Functions to implement:
1. `calculate_emi(loan_amount, interest_rate, tenure_years)` → Returns monthly EMI
2. `check_ltv(property_price, down_payment)` → Returns max loanable amount, validates 80% rule
3. `calculate_upfront_costs(property_price)` → Returns 7% breakdown (4% Transfer + 2% Agency + 1% Misc)
4. `buy_vs_rent_analysis(monthly_rent, property_price, stay_years, income, down_payment)` → Returns recommendation

**Formula**: EMI = P × r × (1+r)^n / ((1+r)^n - 1)
- P = Loan amount
- r = Monthly interest rate (annual/12)
- n = Number of months

### Step 1.3: Groq Agent Setup (agent.py)
**Purpose**: Create agent with function calling using Groq Python SDK

Components:
- Initialize Groq client: `Groq(api_key=os.getenv("GROQ_API_KEY"))`
- Define tools schema (JSON format for function calling)
- Convert math functions to Groq tool definitions
- System prompt: "You are a friendly mortgage advisor helping expats in UAE..."
- Handle tool calls: Execute functions when LLM requests them
- Streaming support: Use `with_streaming_response.create()` for SSE

Key Implementation:
- Use Groq's `tools` parameter in chat completion
- Parse `tool_calls` from response
- Execute functions and send results back to LLM
- Continue conversation with function results

### Step 1.4: Conversation State (state.py)
**Purpose**: Store conversation history per session

Structure:
```python
conversations = {
    "session_id": {
        "messages": [...],  # Chat history
        "created_at": timestamp,
        "user_data": {}     # Extracted: income, property_price, etc.
    }
}
```

Functions:
- `create_session()` → Generate UUID, initialize dict
- `add_message(session_id, role, content)` → Append to history
- `get_history(session_id)` → Return messages for context

### Step 1.5: FastAPI Endpoints (main.py)
**Purpose**: API server with streaming support

Endpoints:
1. `POST /chat` → Accept message, return SSE stream
   - Input: `{session_id, message}`
   - Output: SSE stream of agent response
   - Process: Get history → Call agent → Stream tokens

2. `POST /chat/new` → Create new session
   - Output: `{session_id}`

3. `POST /leads` → Capture lead info
   - Input: `{session_id, name, email, phone}`
   - Output: Success confirmation
   - Action: Append to `leads.json` file

4. `GET /health` → Health check

### Step 1.6: Docker Setup
**Purpose**: Local development environment with Docker Desktop

Files to create:

**Dockerfile** (backend):
```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY ./app /app/app
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

**docker-compose.yml** (root):
```yaml
version: '3.8'
services:
  backend:
    build: ./backend
    ports:
      - "8000:8000"
    env_file:
      - ./backend/.env
    volumes:
      - ./backend/app:/app/app
      - ./backend/leads.json:/app/leads.json
```

**Commands**:
- `docker-compose up --build` → Start backend container
- `docker-compose down` → Stop container
- `docker-compose logs -f` → View logs

---

## Phase 2: Frontend (User Interface)

### Step 2.1: Chat UI Component (components/Chat.tsx)
**Purpose**: Display conversation and handle user input

Features:
- Message list (user/assistant)
- Input field with send button
- Loading indicator during streaming
- Auto-scroll to latest message

State:
- `messages`: Array of {role, content}
- `sessionId`: Current session UUID
- `isLoading`: Streaming status

### Step 2.2: SSE Streaming Client
**Purpose**: Consume streaming responses from backend

Implementation:
- Use `EventSource` or `fetch` with SSE
- Listen for `data` events
- Append tokens to current message
- Handle `done` event to stop streaming

### Step 2.3: Lead Capture (components/LeadCapture.tsx)
**Purpose**: Collect contact info at conversation end

Trigger:
- Agent suggests lead capture (detect in response)
- Or show after 5+ messages

Form fields:
- Name (text)
- Email (email)
- Phone (tel)

Action: POST to `/leads` endpoint

### Step 2.4: Main Page (app/page.tsx)
**Purpose**: Orchestrate chat and lead capture

Layout:
- Header: "UAE Mortgage Assistant"
- Chat component (main area)
- Lead capture modal (conditional)

---

## Phase 3: Integration & Testing

### Step 3.1: Connect Frontend ↔ Backend
- Test SSE streaming works
- Verify function calling triggers math calculations
- Check conversation state persists

### Step 3.2: Test Scenarios
1. **Happy Path**: User provides all info → Gets recommendation → Captures lead
2. **Vague Input**: "I make 20k and want to buy in Marina" → Agent extracts info
3. **Edge Cases**: 
   - Zero income → Graceful error
   - Property too expensive → LTV warning
   - Missing fields → Agent asks follow-ups

### Step 3.3: Error Handling
- Network errors → Show user-friendly message
- LLM failures → Fallback response
- Invalid inputs → Validation messages

---

## Phase 4: Polish & Documentation

### Step 4.1: UI/UX Improvements
- Loading states
- Error messages
- Responsive design
- Typing indicators

### Step 4.2: Code Quality
- Add docstrings
- Modular structure (easy to swap LLM)
- Environment variables for config

### Step 4.3: Documentation
- README.md with:
  - Setup instructions
  - Architecture explanation
  - Function calling code example
  - Deployment guide

---

## Implementation Order (Priority)

1. ✅ **Backend Math Functions** (tools.py) - Foundation
2. ✅ **Docker Setup** (Dockerfile, docker-compose.yml) - Local dev environment
3. ✅ **Groq Agent** (agent.py) - Core AI logic with function calling
4. ✅ **FastAPI Endpoints** (main.py) - API layer with SSE streaming
5. ✅ **Basic Chat UI** (Chat.tsx) - User interface
6. ✅ **SSE Integration** - Streaming
7. ✅ **Lead Capture** - Conversion point
8. ✅ **Testing & Polish** - Edge cases, errors

---

## Key Decisions Made

- **Scenario**: Buy vs Rent (more complete logic provided)
- **Streaming**: SSE (simpler than WebSocket)
- **State**: In-memory (no database needed)
- **Leads**: JSON file (simple storage)
- **Session**: UUID per conversation (no expiry for MVP)
- **AI SDK**: Groq Python SDK (direct, no LangChain abstraction)
- **Deployment**: Frontend on Vercel, Backend on Railway
- **Local Dev**: Docker Desktop with docker-compose

---

## Success Criteria

✅ Math calculations use function calling (no LLM math)  
✅ Streaming responses work  
✅ Agent understands vague inputs  
✅ Lead capture happens at end  
✅ Code is modular (easy to swap LLM)  
✅ Handles edge cases gracefully  

---

## Time Estimate

- Backend: ~4-5 hours
- Frontend: ~3-4 hours
- Integration: ~2 hours
- Polish: ~1-2 hours
- **Total: ~10-12 hours** (within 24h limit)
