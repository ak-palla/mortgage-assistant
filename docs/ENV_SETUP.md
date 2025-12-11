# Environment Variables Setup Guide

This document lists all required environment variables for the Mortgage Assistant application.

## Backend Environment Variables

### Location: `backend/.env`

**Required Variables:**

```bash
# Groq API Key (REQUIRED)
# Get your API key from: https://console.groq.com/keys
GROQ_API_KEY=your_groq_api_key_here

# LangSmith Tracing (Optional but recommended for debugging and proof)
# Get your API key from: https://smith.langchain.com
LANGSMITH_API_KEY=your_langsmith_api_key_here
LANGSMITH_PROJECT=mortgage-assistant
LANGSMITH_TRACING=true
```

### Setup Instructions:

1. Navigate to the backend directory:
   ```bash
   cd backend
   ```

2. Create a `.env` file:
   ```bash
   cp .env.example .env  # If .env.example exists
   # OR create manually
   touch .env
   ```

3. Add your Groq API key:
   ```bash
   echo "GROQ_API_KEY=your_actual_api_key_here" > .env
   ```

4. **Get your Groq API Key:**
   - Visit: https://console.groq.com/keys
   - Sign up/Login
   - Create a new API key
   - Copy and paste it into `.env`

### Docker Usage:

The `docker-compose.yml` automatically loads variables from `backend/.env`:
- The `env_file` directive loads all variables from `./backend/.env`
- The `environment` directive also passes `GROQ_API_KEY` explicitly

---

## Frontend Environment Variables

### Location: `frontend/.env.local`

**Required Variables:**

```bash
# Backend API URL (OPTIONAL - defaults to http://localhost:8000)
NEXT_PUBLIC_API_URL=http://localhost:8000
```

### Setup Instructions:

1. Navigate to the frontend directory:
   ```bash
   cd frontend
   ```

2. Create a `.env.local` file:
   ```bash
   touch .env.local
   ```

3. Add the backend URL:
   ```bash
   # For local development
   echo "NEXT_PUBLIC_API_URL=http://localhost:8000" > .env.local
   
   # For production (after deploying backend to Railway)
   # echo "NEXT_PUBLIC_API_URL=https://your-backend.railway.app" > .env.local
   ```

### Environment-Specific Values:

| Environment | `NEXT_PUBLIC_API_URL` |
|------------|----------------------|
| **Local Development** | `http://localhost:8000` |
| **Production (Railway)** | `https://your-backend.railway.app` |
| **Production (Custom)** | `https://your-backend-domain.com` |

**Note:** The `NEXT_PUBLIC_` prefix is required for Next.js to expose the variable to the browser.

---

## Complete Setup Example

### Backend Setup:

```bash
# 1. Go to backend directory
cd mortgage-assistant/backend

# 2. Create .env file
cat > .env << EOF
GROQ_API_KEY=gsk_your_actual_api_key_here
EOF

# 3. Verify (don't commit this file!)
cat .env
```

### Frontend Setup:

```bash
# 1. Go to frontend directory
cd mortgage-assistant/frontend

# 2. Create .env.local file
cat > .env.local << EOF
NEXT_PUBLIC_API_URL=http://localhost:8000
EOF

# 3. Verify
cat .env.local
```

---

## Production Deployment

### Railway (Backend):

1. In Railway dashboard, go to your project
2. Click on "Variables" tab
3. Add environment variable:
   - **Key:** `GROQ_API_KEY`
   - **Value:** Your Groq API key

### Vercel (Frontend):

1. In Vercel dashboard, go to your project
2. Click on "Settings" → "Environment Variables"
3. Add environment variable:
   - **Key:** `NEXT_PUBLIC_API_URL`
   - **Value:** Your Railway backend URL (e.g., `https://your-backend.railway.app`)
   - **Environment:** Production, Preview, Development (select all)

---

## Security Notes

⚠️ **Important:**

1. **Never commit `.env` files to Git**
   - Backend `.env` is in `.gitignore`
   - Frontend `.env.local` is automatically ignored by Next.js

2. **API Keys are sensitive**
   - Keep your Groq API key secret
   - Don't share it publicly
   - Rotate keys if exposed

3. **Environment Variables**
   - Use different keys for development and production
   - Set up proper secrets management in production

---

## Verification

### Check Backend Environment:

```bash
# From backend directory
cd backend
cat .env
# Should show: GROQ_API_KEY=your_key_here
```

### Check Frontend Environment:

```bash
# From frontend directory
cd frontend
cat .env.local
# Should show: NEXT_PUBLIC_API_URL=http://localhost:8000
```

### Test Backend Connection:

```bash
# Start backend
docker-compose up -d

# Test health endpoint
curl http://localhost:8000/health
# Should return: {"status":"healthy","service":"mortgage-assistant"}
```

---

## Troubleshooting

### Backend Issues:

**Error: "GROQ_API_KEY not set"**
- Check that `backend/.env` exists
- Verify the key is correct (no extra spaces)
- Restart Docker container: `docker-compose restart`

**Error: "Invalid API key"**
- Verify key at https://console.groq.com/keys
- Check for typos in `.env` file
- Ensure no quotes around the key value

### Frontend Issues:

**Error: "Failed to fetch" or CORS errors**
- Check `NEXT_PUBLIC_API_URL` is set correctly
- Verify backend is running
- Check backend CORS settings in `backend/app/main.py`

**Error: "API URL not found"**
- Ensure `.env.local` exists in `frontend/` directory
- Restart Next.js dev server after changing `.env.local`
- Check variable name has `NEXT_PUBLIC_` prefix

---

## Summary

| Component | File | Required Variables |
|-----------|------|-------------------|
| **Backend** | `backend/.env` | `GROQ_API_KEY` (required) |
| **Frontend** | `frontend/.env.local` | `NEXT_PUBLIC_API_URL` (optional, defaults to localhost:8000) |

**Total Required:** 1 variable (GROQ_API_KEY)  
**Total Optional:** 1 variable (NEXT_PUBLIC_API_URL)
