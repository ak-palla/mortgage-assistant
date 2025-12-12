'use client';

import { useState, useEffect, useRef } from 'react';
import Image from 'next/image';

interface Message {
  role: 'user' | 'assistant';
  content: string;
  id: string;
}

interface ChatProps {
  sessionId: string;
  onLeadCapture: () => void;
}

export default function Chat({ sessionId, onLeadCapture }: ChatProps) {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const [currentStreamingMessage, setCurrentStreamingMessage] = useState('');

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, currentStreamingMessage]);

  const sendMessage = async () => {
    if (!input.trim() || isLoading) return;

    const userMessage: Message = {
      role: 'user',
      content: input.trim(),
      id: Date.now().toString(),
    };

    setMessages((prev) => [...prev, userMessage]);
    setInput('');
    setIsLoading(true);
    setError(null);
    setCurrentStreamingMessage('');

    try {
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/chat`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          session_id: sessionId,
          message: userMessage.content,
        }),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const reader = response.body?.getReader();
      const decoder = new TextDecoder();

      if (!reader) {
        throw new Error('No response body');
      }

      let buffer = '';
      let accumulatedContent = '';

      while (true) {
        const { done, value } = await reader.read();

        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split('\n');
        buffer = lines.pop() || '';

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            try {
              const data = JSON.parse(line.slice(6));

              if (data.type === 'content') {
                accumulatedContent += data.content;
                setCurrentStreamingMessage(accumulatedContent);
              } else if (data.type === 'done') {
                // Save the complete message
                const assistantMessage: Message = {
                  role: 'assistant',
                  content: accumulatedContent,
                  id: (Date.now() + 1).toString(),
                };
                setMessages((prev) => {
                  const newMessages = [...prev, assistantMessage];
                  // Check if we should show lead capture (after a few messages)
                  if (newMessages.length >= 4) {
                    setTimeout(() => {
                      onLeadCapture();
                    }, 2000);
                  }
                  return newMessages;
                });
                setCurrentStreamingMessage('');
                accumulatedContent = '';
              } else if (data.type === 'error') {
                throw new Error(data.content);
              }
            } catch (e) {
              console.error('Error parsing SSE data:', e);
            }
          }
        }
      }
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to send message';
      setError(errorMessage);
      console.error('Chat error:', err);
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  // Format agent response text
  const formatAgentResponse = (text: string): string => {
    // Preserve line breaks and format the text
    let formatted = text.trim();

    // Add spacing after periods if followed by uppercase (new sentences)
    formatted = formatted.replace(/\.([A-Z])/g, '. $1');

    // Ensure double line breaks for paragraphs
    formatted = formatted.replace(/\n\n+/g, '\n\n');

    // Format numbers with commas (AED amounts)
    formatted = formatted.replace(/(\d+)(\s*AED)/g, (match, num, suffix) => {
      return Number(num).toLocaleString() + suffix;
    });

    // Format standalone large numbers
    formatted = formatted.replace(/\b(\d{4,})\b/g, (match) => {
      return Number(match).toLocaleString();
    });

    return formatted;
  };

  return (
    <div className="flex h-full bg-white/50 dark:bg-slate-900/50 relative">
      <div className="flex flex-col flex-1 h-full min-w-0">
        {/* Messages */}
        <div className="flex-1 overflow-y-auto p-4 sm:p-6 space-y-6 scroll-smooth">
          {messages.length === 0 && (
            <div className="flex flex-col items-center justify-center h-full text-center p-8 opacity-0 animate-in fade-in slide-in-from-bottom-4 duration-700 fill-mode-forwards" style={{ animationDelay: '0.2s', animationFillMode: 'forwards' }}>
              <div className="flex items-center justify-center mb-6">
                <Image
                  src="/logo.png"
                  alt="AskRivo"
                  width={80}
                  height={80}
                  className="object-contain drop-shadow-xl"
                  priority
                />
              </div>
              <h2 className="text-3xl font-bold mb-3 bg-clip-text text-transparent bg-gradient-to-r from-primary to-blue-600">
                AskRivo
              </h2>
              <p className="text-muted-foreground max-w-md text-lg mb-8">
                Your AI partner for smarter property decisions in the UAE.
              </p>
            </div>
          )}

          {messages.map((message) => (
            <div
              key={message.id}
              className={`flex gap-4 ${message.role === 'user' ? 'flex-row-reverse' : 'flex-row'} animate-in slide-in-from-bottom-2 fade-in duration-300`}
            >
              {/* Avatar */}
              <div className={`w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0 mt-1 ${message.role === 'user'
                ? 'bg-primary text-primary-foreground'
                : 'bg-emerald-600 text-white shadow-sm'
                }`}>
                {message.role === 'user' ? (
                  <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M19 21v-2a4 4 0 0 0-4-4H9a4 4 0 0 0-4 4v2" /><circle cx="12" cy="7" r="4" /></svg>
                ) : (
                  <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M12 2a3 3 0 0 0-3 3v7a3 3 0 0 0 6 0V5a3 3 0 0 0-3-3Z" /><path d="M19 10v2a7 7 0 0 1-14 0v-2" /><line x1="12" x2="12" y1="19" y2="22" /></svg>
                )}
              </div>

              {/* Message bubble */}
              <div
                className={`max-w-[85%] rounded-2xl px-5 py-3 shadow-sm ${message.role === 'user'
                  ? 'bg-primary text-primary-foreground rounded-tr-sm'
                  : 'bg-white dark:bg-slate-800 text-foreground border border-border/50 rounded-tl-sm'
                  }`}
              >
                <div className={`text-[15px] ${message.role === 'assistant' ? 'leading-7' : 'leading-relaxed'
                  }`}>
                  {message.role === 'assistant'
                    ? formatAgentResponse(message.content)
                    : message.content
                  }
                </div>
              </div>
            </div>
          ))}

          {/* Streaming message */}
          {currentStreamingMessage && (
            <div className="flex gap-4 animate-in fade-in duration-200">
              <div className="w-8 h-8 rounded-full bg-emerald-600 text-white flex items-center justify-center flex-shrink-0 mt-1 shadow-sm">
                <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M12 2a3 3 0 0 0-3 3v7a3 3 0 0 0 6 0V5a3 3 0 0 0-3-3Z" /><path d="M19 10v2a7 7 0 0 1-14 0v-2" /><line x1="12" x2="12" y1="19" y2="22" /></svg>
              </div>

              <div className="max-w-[85%] rounded-2xl rounded-tl-sm px-5 py-3 bg-white dark:bg-slate-800 text-foreground border border-border/50 shadow-sm">
                <div className="text-[15px] leading-7">
                  {formatAgentResponse(currentStreamingMessage)}
                  <span className="inline-block w-2 h-4 ml-1 align-middle bg-primary/50 animate-pulse rounded-sm"></span>
                </div>
              </div>
            </div>
          )}

          {/* Error message */}
          {error && (
            <div className="flex justify-center my-4">
              <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 text-red-600 dark:text-red-400 px-4 py-2 rounded-lg text-sm flex items-center gap-2">
                <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><circle cx="12" cy="12" r="10" /><line x1="12" x2="12" y1="8" y2="12" /><line x1="12" x2="12.01" y1="16" y2="16" /></svg>
                {error}
              </div>
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>

        {/* Input */}
        <div className="p-4 sm:p-6 bg-white/80 dark:bg-slate-900/80 backdrop-blur-md border-t border-border/50">
          <div className="relative flex items-center max-w-4xl mx-auto shadow-sm rounded-xl overflow-hidden focus-within:shadow-md focus-within:ring-2 focus-within:ring-primary/20 transition-all duration-200 bg-white dark:bg-slate-800 border border-input">
            <input
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={handleKeyPress}
              placeholder="Type your message..."
              disabled={isLoading}
              className="flex-1 bg-transparent px-5 py-4 focus:outline-none text-base placeholder:text-muted-foreground/60"
            />
            <button
              onClick={sendMessage}
              disabled={isLoading || !input.trim()}
              className="mr-2 p-2 rounded-lg text-white bg-primary hover:bg-primary/90 disabled:opacity-50 disabled:cursor-not-allowed transition-all duration-200 shadow-sm aspect-square flex items-center justify-center"
            >
              {isLoading ? (
                <div className="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
              ) : (
                <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><line x1="22" x2="11" y1="2" y2="13" /><polygon points="22 2 15 22 11 13 2 9 22 2" /></svg>
              )}
            </button>
          </div>
          <p className="text-center text-xs text-muted-foreground mt-3">
            AI can make mistakes. Please verify important financial information.
          </p>
        </div>
      </div>

      {/* Templates Sidebar */}
      <div className="w-[300px] border-l border-white/20 bg-white/40 dark:bg-slate-900/40 backdrop-blur-md hidden lg:flex flex-col h-full">
        <div className="p-4 border-b border-white/10 flex items-center gap-2">
          <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="text-primary"><rect width="18" height="18" x="3" y="3" rx="2" /><path d="M9 3v18" /><path d="m14 9 3 3-3 3" /></svg>
          <h3 className="text-sm font-semibold text-foreground">Scenarios</h3>
        </div>

        <div className="flex-1 overflow-y-auto p-4 space-y-3 custom-scrollbar">
          {[
            {
              title: "Simple EMI Calculation",
              text: "Calculate EMI for 1.5M loan over 15 years at 4.5%",
              icon: <path d="M12 2v20M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6" />
            },
            {
              title: "LTV Validation",
              text: "I want to buy a 1.8M apartment. I can put down 400k",
              icon: <><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14" /><path d="M22 4 12 14.01l-3-3" /></>
            },
            {
              title: "Upfront Costs",
              text: "Tell me about all the fees for a 3.5M property purchase",
              icon: <><path d="M2 12h10" /><path d="M9 4v16" /><path d="m3 9 3 3-3 3" /><path d="M12 20h9" /><path d="M16.5 3.5a2.121 2.121 0 0 1 3 3L7 19l-4 1 1-4L16.5 3.5z" /></>
            },
            {
              title: "Buy vs Rent Analysis",
              text: "Should I buy or rent? I make 25k per month, property is 2M, I have 500k down payment, current rent is 8k, and I plan to stay 7 years",
              icon: <><path d="M3 21h18" /><path d="M5 21V7l8-4 8 4v14" /><path d="M17 21v-8.5a1.5 1.5 0 0 0-3 0V21" /></>
            },
            {
              title: "Vague: Should I buy?",
              text: "Should I buy a property?",
              icon: <><circle cx="12" cy="12" r="10" /><path d="M9.09 9a3 3 0 0 1 5.83 1c0 2-3 3-3 3" /><path d="M12 17h.01" /></>
            },
            {
              title: "Vague: Income + Savings",
              text: "I have 500k saved and make 25k per month",
              icon: <path d="M12 2v20M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6" />
            },
            {
              title: "Full Journey Start",
              text: "Hi, I'm thinking about buying property in Dubai",
              icon: <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z" />
            }
          ].map((template, i) => (
            <button
              key={i}
              onClick={() => setInput(template.text)}
              className="w-full text-left p-3 rounded-xl bg-white/50 dark:bg-slate-800/50 border border-white/20 shadow-sm hover:shadow-md hover:border-primary/50 hover:bg-white dark:hover:bg-slate-800 transition-all duration-200 group relative overflow-hidden"
            >
              <div className="flex items-start gap-3">
                <div className="mt-1 p-1.5 rounded-lg bg-primary/10 text-primary group-hover:bg-primary group-hover:text-white transition-colors duration-200">
                  <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                    {template.icon}
                  </svg>
                </div>
                <div>
                  <h4 className="text-xs font-semibold text-foreground/80 group-hover:text-primary mb-1 transition-colors">{template.title}</h4>
                  <p className="text-xs text-muted-foreground line-clamp-2 leading-relaxed">
                    {template.text}
                  </p>
                </div>
              </div>
            </button>
          ))}
        </div>
      </div>
    </div>
  );
}
