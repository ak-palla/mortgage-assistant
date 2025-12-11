'use client';

import { useState, useEffect } from 'react';
import Image from 'next/image';
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
      <div className="flex items-center justify-center min-h-screen bg-background">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-primary mx-auto"></div>
          <p className="mt-4 text-muted-foreground font-medium">Initializing Mortgage Assistant...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="flex flex-col h-screen overflow-hidden relative selection:bg-accent selection:text-accent-foreground">
      {/* Background decoration */}
      <div className="fixed inset-0 pointer-events-none z-0">
        <div className="absolute -top-20 -right-20 w-96 h-96 bg-primary/10 rounded-full blur-3xl opacity-50"></div>
        <div className="absolute -bottom-20 -left-20 w-80 h-80 bg-blue-500/10 rounded-full blur-3xl opacity-50"></div>
      </div>

      {/* Header */}
      <header className="fixed top-0 left-0 right-0 z-20 glass-panel border-b border-white/20">
        <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Image
              src="/logo.png"
              alt="Logo"
              width={40}
              height={40}
              className="w-10 h-10 object-contain drop-shadow-md"
            />
            <div>
              <h1 className="text-lg font-bold text-foreground leading-tight">UAE Mortgage Assistant</h1>
            </div>
          </div>
          <p className="hidden sm:block text-sm text-muted-foreground font-medium bg-secondary/50 px-3 py-1 rounded-full border border-white/10">
            Powered by AI
          </p>
        </div>
      </header>

      {/* Chat Area */}
      <main className="flex-1 overflow-hidden w-full max-w-5xl mx-auto pt-20 pb-4 px-2 sm:px-4 z-10">
        <div className="h-full w-full bg-white/80 dark:bg-slate-900/80 backdrop-blur-md rounded-2xl shadow-xl border border-white/20 overflow-hidden flex flex-col transition-all duration-300">
          <Chat
            sessionId={sessionId}
            onLeadCapture={() => !leadSubmitted && setShowLeadCapture(true)}
          />
        </div>
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
        <div className="fixed bottom-8 right-8 z-50 animate-in slide-in-from-bottom-4 fade-in duration-300">
          <div className="glass-panel text-primary-foreground bg-primary px-6 py-4 rounded-xl shadow-lg shadow-primary/20 flex items-center gap-3">
            <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
            </svg>
            <span className="font-medium">Details received! We&apos;ll be in touch soon.</span>
          </div>
        </div>
      )}
    </div>
  );
}
