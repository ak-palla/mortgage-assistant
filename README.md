# UAE Mortgage Assistant - "The Anti-Calculator"

> **Status: ✅ Assignment Completed & Ready for Deployment**

A conversational AI agent that helps UAE expats navigate property decisions through natural conversation, not robotic calculators. Built as part of the CoinedOne AI Engineering Challenge.

## 🎯 Project Overview

This is a **functional conversational mortgage assistant** that acts like a "Smart Friend" rather than a calculator. It guides users through the financial maze of UAE property purchases using natural conversation, while ensuring all calculations are accurate through deterministic tool calling.

### Key Features

- ✅ **Conversational Interface**: Natural chat UI with SSE streaming
- ✅ **Intent Recognition**: Understands vague inputs like "I make 20k and want to buy in Marina"
- ✅ **Unobtrusive Data Collection**: Gathers information naturally through conversation
- ✅ **Accurate Math**: All calculations via function calling (no LLM hallucinations)
- ✅ **Lead Capture**: Seamlessly guides users to provide contact details
- ✅ **Buy vs Rent Analysis**: Intelligent recommendations based on user situation

---

## 🏗️ Architecture

### Tech Stack

- **Frontend**: Next.js 14+ (App Router) with TypeScript
- **Backend**: FastAPI (Python) with SSE streaming
- **AI Provider**: Groq API with Llama 3.3 70B Versatile
- **State Management**: In-memory conversation state (Python dict)
- **Tracing**: LangSmith for observability
- **Deployment**: Railway (backend) + Vercel (frontend)

### Why This Stack?

**LLM Choice: Groq + Llama 3.3 70B**
- **Speed**: Groq's inference engine provides sub-second responses
- **Function Calling**: Native support for tool/function calling
- **Cost-Effective**: Competitive pricing for high-volume usage
- **Reliability**: Stable API with good error handling

**Framework: Direct Groq SDK (No LangChain)**
- **Simplicity**: Direct API calls without abstraction overhead
- **Control**: Full control over tool calling and response handling
- **Performance**: Lower latency without framework overhead
- **Transparency**: Clear code flow for evaluation

**Frontend: Next.js App Router**
- **SSE Streaming**: Native support for Server-Sent Events
- **Type Safety**: TypeScript ensures type safety
- **Modern UX**: React Server Components for optimal performance

---

## 🧮 The Math: Solving the Hallucination Problem

**Critical Requirement**: LLMs are notoriously bad at arithmetic. All calculations MUST be done via deterministic functions, not LLM math.

### Tool Calling Implementation

The system uses **function calling** to ensure accurate calculations. Here's how it works:

#### 1. Tool Definition (Function Schema)

```python
# backend/app/agent.py
TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "calculate_emi",
            "description": "Calculate Equated Monthly Installment (EMI) for a mortgage loan...",
            "parameters": {
                "type": "object",
                "properties": {
                    "loan_amount": {"type": "number", "description": "Principal loan amount in AED"},
                    "interest_rate": {"type": "number", "description": "Annual interest rate (e.g., 4.5 for 4.5%)"},
                    "tenure_years": {"type": "integer", "description": "Loan tenure in years (maximum 25 years)"}
                },
                "required": ["loan_amount", "tenure_years"]
            }
        }
    }
    # ... other tools (check_ltv, calculate_upfront_costs, buy_vs_rent_analysis)
]
```

#### 2. Pure Python Math Function

```python
# backend/app/tools.py
@trace_tool_execution("calculate_emi")
def calculate_emi(loan_amount: float, interest_rate: float, tenure_years: int) -> Dict[str, Any]:
    """
    Calculate Equated Monthly Installment (EMI).
    
    Formula: EMI = P × r × (1+r)^n / ((1+r)^n - 1)
    Where:
    - P = Loan amount
    - r = Monthly interest rate (annual/12)
    - n = Number of months
    """
    if loan_amount <= 0:
        return {"error": "Loan amount must be positive"}
    
    # Convert to monthly
    monthly_rate = (interest_rate / 100) / 12
    num_months = tenure_years * 12
    
    # Calculate EMI using standard formula
    if monthly_rate == 0:
        emi = loan_amount / num_months
    else:
        emi = loan_amount * monthly_rate * ((1 + monthly_rate) ** num_months) / (((1 + monthly_rate) ** num_months) - 1)
    
    total_amount = emi * num_months
    total_interest = total_amount - loan_amount
    
    return {
        "emi": round(emi, 2),
        "total_amount": round(total_amount, 2),
        "total_interest": round(total_interest, 2),
        "loan_amount": loan_amount,
        "interest_rate": interest_rate,
        "tenure_years": tenure_years,
        "tenure_months": num_months
    }
```

#### 3. Tool Execution Flow

```python
# backend/app/main.py
# When Groq returns tool_calls, we execute them:

for tool_call, tool_name, arguments in valid_tool_calls:
    # Execute the deterministic function (not LLM math!)
    tool_result = execute_tool(tool_name, arguments)
    
    # Add result back to conversation for LLM to interpret
    messages.append({
        "role": "tool",
        "tool_call_id": tool_call.id,
        "content": json.dumps(tool_result)
    })

# LLM then generates natural language response from tool results
```

**Result**: The LLM handles empathy and conversation, but ALL math is done by deterministic Python functions. Zero hallucinations.

### Available Tools

1. **`calculate_emi`**: EMI calculation using standard formula
2. **`check_ltv`**: Validates 80% LTV rule for UAE expats
3. **`calculate_upfront_costs`**: Calculates 7% upfront costs (4% transfer + 2% agency + 1% misc)
4. **`buy_vs_rent_analysis`**: Analyzes buy vs rent decision with heuristics

---

## 🚀 The Speed Run: AI-Assisted Development

This project was built using **AI-native development tools** to accelerate the build:

- **Cursor**: Primary IDE with AI code completion and chat
- **Claude (via Cursor)**: Architecture decisions, code generation, debugging
- **GitHub Copilot**: Inline code suggestions
- **AI-Assisted Debugging**: Used AI to identify and fix tool calling issues

**Time to Build**: ~24 hours (assignment requirement)

**Key AI Assistance**:
- Generated FastAPI boilerplate with SSE streaming
- Created tool calling schema definitions
- Debugged Groq API integration issues
- Optimized system prompts for better tool usage
- Generated frontend components with TypeScript

---

## 📋 Domain Logic (UAE Mortgage Rules)

All domain rules are enforced via tool validation:

1. **Maximum LTV**: Expats can only borrow up to **80%** of property value
2. **Upfront Costs**: **7%** total (4% transfer fee + 2% agency fee + 1% misc)
3. **Interest Rate**: Standard market rate of **4.5%** (configurable)
4. **Max Tenure**: **25 years**

**Buy vs Rent Heuristics**:
- Stay < 3 years → Advise Renting (transaction fees kill profit)
- Stay > 5 years → Advise Buying (equity buildup beats rent)
- 3-5 years → Compare monthly costs

---

## 🛠️ Setup Instructions

### Prerequisites

- Python 3.9+
- Node.js 18+
- Docker (optional, for local development)
- Groq API key ([Get one here](https://console.groq.com/keys))

### Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Create .env file
echo "GROQ_API_KEY=your_groq_api_key_here" > .env

# Run locally
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Create .env.local file
echo "NEXT_PUBLIC_API_URL=http://localhost:8000" > .env.local

# Run development server
npm run dev
```

### Docker Setup (Recommended)

```bash
# From project root
docker-compose up --build
```

Backend: http://localhost:8000  
Frontend: http://localhost:3000

---

## 🚢 Deployment

### Backend Deployment (Railway)

1. **Push code to GitHub** (create public repo)
2. **Connect Railway to GitHub**:
   - Go to [Railway](https://railway.app)
   - New Project → Deploy from GitHub repo
   - Select `mortgage-assistant` repo
3. **Configure Environment Variables**:
   - `GROQ_API_KEY`: Your Groq API key
   - (Optional) `LANGSMITH_API_KEY`: For tracing
4. **Set Root Directory**: `backend`
5. **Deploy**: Railway will auto-detect FastAPI and deploy

**Railway will provide**: `https://your-backend.railway.app`

### Frontend Deployment (Vercel)

1. **Connect Vercel to GitHub**:
   - Go to [Vercel](https://vercel.com)
   - Import Project → Select GitHub repo
   - Root Directory: `frontend`
2. **Configure Environment Variables**:
   - `NEXT_PUBLIC_API_URL`: Your Railway backend URL
     - Example: `https://your-backend.railway.app`
3. **Deploy**: Vercel will auto-detect Next.js and deploy

**Vercel will provide**: `https://your-app.vercel.app`

### Post-Deployment

1. Update CORS in `backend/app/main.py`:
   ```python
   allow_origins=["https://your-app.vercel.app"]
   ```
2. Redeploy backend
3. Test the live application

---

## 📁 Project Structure

```
mortgage-assistant/
├── backend/
│   ├── app/
│   │   ├── main.py          # FastAPI app with SSE streaming
│   │   ├── agent.py          # Groq AI agent with function calling
│   │   ├── tools.py          # Math functions (EMI, LTV, etc.)
│   │   ├── state.py          # In-memory conversation state
│   │   ├── models.py         # Pydantic request/response models
│   │   └── tracing.py        # LangSmith tracing setup
│   ├── Dockerfile
│   ├── requirements.txt
│   └── README.md
├── frontend/
│   ├── app/
│   │   ├── page.tsx         # Main chat page
│   │   ├── components/
│   │   │   ├── Chat.tsx     # Chat UI with SSE streaming
│   │   │   └── LeadCapture.tsx  # Lead capture modal
│   │   └── lib/
│   │       └── api.ts        # API utility functions
│   ├── package.json
│   └── README.md
├── docs/
│   ├── assignment.md         # Original assignment brief
│   ├── ENV_SETUP.md         # Environment setup guide
│   └── IMPLEMENTATION_PLAN.md
├── docker-compose.yml
└── README.md                 # This file
```

---

## 🧪 Testing

### Test Scenarios

1. **Happy Path**: User provides all info → Gets recommendation → Captures lead
2. **Vague Input**: "I make 20k and want to buy in Marina" → Agent extracts info
3. **Edge Cases**:
   - Zero income → Graceful error handling
   - Property too expensive → LTV warning
   - Missing fields → Agent asks follow-ups

### Manual Testing

```bash
# Test backend health
curl http://localhost:8000/health

# Create session
curl -X POST http://localhost:8000/chat/new

# Send message (replace session_id)
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"session_id": "your-session-id", "message": "I make 50k AED per month"}'
```

---

## 📊 Evaluation Criteria Met

### 1. Architecture & Reliability (40%)
- ✅ **Hallucination Problem Solved**: All math via deterministic functions
- ✅ **Conversation State**: In-memory state management with session IDs
- ✅ **Edge Case Handling**: Validation for invalid inputs, zero values, etc.

### 2. Product Sense (30%)
- ✅ **Human-like**: Empathetic system prompt, natural conversation flow
- ✅ **Conversion Point**: Lead capture modal after 4+ messages
- ✅ **UI/UX**: Clean, responsive chat interface with message labels

### 3. Velocity & Tooling (20%)
- ✅ **24-Hour Build**: Completed within assignment timeframe
- ✅ **AI Tools Used**: Cursor, Claude, GitHub Copilot

### 4. Code Quality (10%)
- ✅ **Modular**: Easy to swap LLM (just change `client` in `agent.py`)
- ✅ **Clean Code**: Type hints, docstrings, error handling
- ✅ **Separation of Concerns**: Tools, agent, and API layers separated

---

## 🔑 Environment Variables

### Backend (`.env`)
```bash
GROQ_API_KEY=your_groq_api_key_here
LANGSMITH_API_KEY=your_langsmith_key_here  # Optional
LANGSMITH_PROJECT=mortgage-assistant        # Optional
LANGSMITH_TRACING=true                      # Optional
```

### Frontend (`.env.local`)
```bash
NEXT_PUBLIC_API_URL=http://localhost:8000  # Local
# Or for production:
# NEXT_PUBLIC_API_URL=https://your-backend.railway.app
```

---

## 📝 API Endpoints

### `GET /health`
Health check endpoint.

### `POST /chat/new`
Create a new conversation session.
```json
Response: {"session_id": "uuid"}
```

### `POST /chat`
Send a message and receive SSE stream.
```json
Request: {
  "session_id": "uuid",
  "message": "I want to buy a 2M AED apartment"
}
Response: SSE stream with type: 'content' or 'done'
```

### `POST /leads`
Capture lead information.
```json
Request: {
  "session_id": "uuid",
  "name": "John Doe",
  "email": "john@example.com",
  "phone": "+971501234567"
}
```

---

## 🎓 Key Learnings

1. **Function Calling is Critical**: Prevents LLM hallucinations in calculations
2. **SSE Streaming**: Better UX than polling for real-time responses
3. **Tool Validation**: Always validate tool arguments before execution
4. **Fallback Responses**: Handle empty LLM responses gracefully
5. **Temperature Matters**: Lower temperature (0.3) for more deterministic tool usage

---

## 📄 License

This project was built as part of the CoinedOne AI Engineering Challenge.

---

## 👤 Author

Built for CoinedOne Founder's Office AI Engineering Challenge.

**Submission Status**: ✅ **Completed & Ready for Deployment**

---

## 🔗 Links

- **Backend API**: Deploy on [Railway](https://railway.app)
- **Frontend**: Deploy on [Vercel](https://vercel.com)
- **Groq API**: [console.groq.com](https://console.groq.com)
- **LangSmith**: [smith.langchain.com](https://smith.langchain.com) (for tracing)

---

**Ready to deploy!** 🚀
