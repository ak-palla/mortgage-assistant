'use client';

import { useState, useEffect } from 'react';
import Chat from './components/Chat';
import LeadCapture from './components/LeadCapture';

export default function Home() {
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [showLeadCapture, setShowLeadCapture] = useState(false);
  const [leadSubmitted, setLeadSubmitted] = useState(false);
  const [isClient, setIsClient] = useState(false);

  useEffect(() => {
    setIsClient(true);
    // Create a new session on mount
    const createSession = async () => {
      try {
        const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
        const response = await fetch(`${apiUrl}/chat/new`, {
          method: 'POST',
        });

        if (!response.ok) {
          throw new Error('Failed to create session');
        }

        const data = await response.json();
        setSessionId(data.session_id);
      } catch (error) {
        console.error('Error creating session:', error);
      }
    };

    createSession();
  }, []);

  if (!isClient || !sessionId) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500 mx-auto"></div>
          <p className="mt-4 text-gray-600">Initializing chat...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="flex flex-col h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white border-b shadow-sm">
        <div className="max-w-4xl mx-auto px-4 py-4">
          <h1 className="text-2xl font-bold text-gray-900">UAE Mortgage Assistant</h1>
          <p className="text-sm text-gray-600">Your smart friend for property decisions</p>
        </div>
      </header>

      {/* Chat Area */}
      <main className="flex-1 overflow-hidden max-w-4xl w-full mx-auto bg-white shadow-lg my-4 rounded-lg">
        <Chat
          sessionId={sessionId}
          onLeadCapture={() => !leadSubmitted && setShowLeadCapture(true)}
        />
      </main>

      {/* Lead Capture Modal */}
      {showLeadCapture && (
        <LeadCapture
          sessionId={sessionId}
          onClose={() => setShowLeadCapture(false)}
          onSuccess={() => {
            setLeadSubmitted(true);
            setShowLeadCapture(false);
          }}
        />
      )}

      {/* Success Message */}
      {leadSubmitted && (
        <div className="fixed bottom-4 right-4 bg-green-500 text-white px-6 py-3 rounded-lg shadow-lg">
          Thank you! We&apos;ll be in touch soon.
        </div>
      )}
    </div>
  );
}
