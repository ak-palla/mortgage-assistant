# Mortgage Assistant Frontend

Next.js frontend for the UAE Mortgage Assistant application.

## Features

- ✅ Real-time chat interface with SSE streaming
- ✅ Lead capture modal
- ✅ Responsive design with Tailwind CSS
- ✅ TypeScript for type safety

## Setup

### 1. Install Dependencies

```bash
npm install
```

### 2. Environment Variables

Create a `.env.local` file:

```bash
NEXT_PUBLIC_API_URL=http://localhost:8000
```

For production, update this to your backend URL (e.g., Railway deployment).

### 3. Run Development Server

```bash
npm run dev
```

Open [http://localhost:3000](http://localhost:3000) in your browser.

## Project Structure

```
frontend/
├── app/
│   ├── components/
│   │   ├── Chat.tsx          # Chat UI with SSE streaming
│   │   └── LeadCapture.tsx    # Lead capture modal
│   ├── lib/
│   │   └── api.ts             # API utility functions
│   ├── page.tsx               # Main page
│   └── globals.css             # Global styles
├── public/                     # Static assets
└── package.json
```

## Components

### Chat Component
- Displays conversation messages
- Handles SSE streaming from backend
- Auto-scrolls to latest message
- Shows loading states

### Lead Capture Component
- Modal form for collecting contact info
- Triggers after 4+ messages
- Submits to backend `/leads` endpoint

## Deployment

### Vercel (Recommended)

1. Push code to GitHub
2. Import project in Vercel
3. Set environment variable: `NEXT_PUBLIC_API_URL` (your backend URL)
4. Deploy

### Manual Build

```bash
npm run build
npm start
```

## API Integration

The frontend connects to the FastAPI backend at:
- `POST /chat/new` - Create new session
- `POST /chat` - Send message (SSE streaming)
- `POST /leads` - Submit lead information

## Notes

- Backend must be running on the configured API URL
- CORS is configured in the backend for `localhost:3000`
- For production, update CORS origins in backend
