/**
 * API configuration and utility functions
 */

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export async function createSession(): Promise<string> {
  const response = await fetch(`${API_URL}/chat/new`, {
    method: 'POST',
  });

  if (!response.ok) {
    throw new Error('Failed to create session');
  }

  const data = await response.json();
  return data.session_id;
}

export async function sendMessage(sessionId: string, message: string): Promise<Response> {
  return fetch(`${API_URL}/chat`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      session_id: sessionId,
      message,
    }),
  });
}

export async function submitLead(sessionId: string, leadData: {
  name: string;
  email: string;
  phone: string;
}): Promise<void> {
  const response = await fetch(`${API_URL}/leads`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      session_id: sessionId,
      ...leadData,
    }),
  });

  if (!response.ok) {
    const errorData = await response.json();
    throw new Error(errorData.detail || 'Failed to submit lead');
  }
}
