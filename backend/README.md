# Mortgage Assistant Backend

FastAPI backend with Groq AI SDK for conversational mortgage advisor.

## Features

- ✅ Groq AI SDK integration with function calling
- ✅ SSE streaming responses
- ✅ In-memory conversation state management
- ✅ Math functions for EMI, LTV, upfront costs, buy vs rent analysis
- ✅ Lead capture endpoint
- ✅ Docker support for local development

## Setup

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Environment Variables

Create a `.env` file:

```bash
GROQ_API_KEY=your_groq_api_key_here
```

Get your API key from: https://console.groq.com/keys

### 3. Run with Docker (Recommended)

```bash
# From project root
docker-compose up --build

# Or run in background
docker-compose up -d
```

### 4. Run Locally (Alternative)

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

## API Endpoints

### Health Check
```
GET /health
```

### Create New Session
```
POST /chat/new
Response: {"session_id": "uuid"}
```

### Chat (Streaming)
```
POST /chat
Body: {
  "session_id": "uuid",
  "message": "I want to buy a 2M AED apartment"
}
Response: SSE stream
```

### Capture Lead
```
POST /leads
Body: {
  "session_id": "uuid",
  "name": "John Doe",
  "email": "john@example.com",
  "phone": "+971501234567"
}
```

## Available Tools (Function Calling)

1. **calculate_emi** - Calculate monthly EMI
2. **check_ltv** - Validate LTV ratio (max 80% for expats)
3. **calculate_upfront_costs** - Calculate 7% upfront costs
4. **buy_vs_rent_analysis** - Analyze buy vs rent decision

## Testing

Test the API with curl:

```bash
# Create session
curl -X POST http://localhost:8000/chat/new

# Chat (non-streaming test)
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"session_id": "your-session-id", "message": "Hello"}'
```

## Architecture

- **app/main.py** - FastAPI application and endpoints
- **app/agent.py** - Groq AI agent with function calling
- **app/tools.py** - Math calculation functions
- **app/state.py** - In-memory conversation state
- **app/models.py** - Pydantic request/response models

## Notes

- Conversation state is stored in-memory (lost on restart)
- Leads are saved to `leads.json` file
- SSE streaming is used for real-time responses
- Tool calling ensures accurate math calculations (no LLM hallucinations)
