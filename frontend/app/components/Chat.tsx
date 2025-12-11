'use client';

import { useState, useEffect, useRef } from 'react';

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
    <div className="flex flex-col h-full">
      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.length === 0 && (
          <div className="text-center text-gray-500 mt-8">
            <h2 className="text-2xl font-bold mb-2">UAE Mortgage Assistant</h2>
            <p>Ask me anything about buying a property in UAE!</p>
            <p className="text-sm mt-2">Try: &quot;I make 20k a month and want to buy in Marina&quot;</p>
          </div>
        )}

        {messages.map((message) => (
          <div
            key={message.id}
            className={`flex flex-col ${message.role === 'user' ? 'items-end' : 'items-start'}`}
          >
            {/* Label */}
            <div className={`text-xs font-semibold mb-1 px-2 ${
              message.role === 'user' ? 'text-blue-600' : 'text-gray-600'
            }`}>
              {message.role === 'user' ? 'User' : 'Agent'}
            </div>
            
            {/* Message bubble */}
            <div
              className={`max-w-[80%] rounded-lg px-4 py-2 ${
                message.role === 'user'
                  ? 'bg-blue-500 text-white'
                  : 'bg-gray-100 text-gray-900'
              }`}
            >
              <div className={`text-sm whitespace-pre-wrap ${
                message.role === 'assistant' ? 'leading-relaxed' : ''
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
          <div className="flex flex-col items-start">
            {/* Label */}
            <div className="text-xs font-semibold mb-1 px-2 text-gray-600">
              Agent
            </div>
            
            {/* Message bubble */}
            <div className="max-w-[80%] rounded-lg px-4 py-2 bg-gray-100 text-gray-900">
              <div className="text-sm whitespace-pre-wrap leading-relaxed">
                {formatAgentResponse(currentStreamingMessage)}
                <span className="animate-pulse">▋</span>
              </div>
            </div>
          </div>
        )}

        {/* Error message */}
        {error && (
          <div className="flex justify-center">
            <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-2 rounded">
              {error}
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Input */}
      <div className="border-t p-4">
        <div className="flex gap-2">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyPress={handleKeyPress}
            placeholder="Type your message..."
            disabled={isLoading}
            className="flex-1 rounded-lg border border-gray-300 px-4 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:bg-gray-100"
          />
          <button
            onClick={sendMessage}
            disabled={isLoading || !input.trim()}
            className="rounded-lg bg-blue-500 px-6 py-2 text-white hover:bg-blue-600 focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:bg-gray-400 disabled:cursor-not-allowed"
          >
            {isLoading ? 'Sending...' : 'Send'}
          </button>
        </div>
      </div>
    </div>
  );
}
