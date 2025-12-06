/**
 * AUREON Chat Service
 * 
 * Handles streaming chat with the AUREON AI via edge function,
 * passing ecosystem context for quantum-aware responses.
 */

import { supabase } from '@/integrations/supabase/client';
import { ChatMessage, ChatStreamChunk } from '@/types';
import { EcosystemContext } from './ecosystemContextBuilder';

const CHAT_URL = `${import.meta.env.VITE_SUPABASE_URL}/functions/v1/aureon-chat`;

/**
 * Stream chat responses from AUREON with ecosystem context
 */
export async function* streamAureonChat(
  messages: ChatMessage[],
  ecosystemContext: EcosystemContext | null
): AsyncGenerator<ChatStreamChunk> {
  try {
    const { data: { session } } = await supabase.auth.getSession();
    
    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
    };
    
    // Add auth header if user is logged in
    if (session?.access_token) {
      headers['Authorization'] = `Bearer ${session.access_token}`;
    } else {
      // Use anon key for unauthenticated requests
      headers['Authorization'] = `Bearer ${import.meta.env.VITE_SUPABASE_PUBLISHABLE_KEY}`;
    }

    const response = await fetch(CHAT_URL, {
      method: 'POST',
      headers,
      body: JSON.stringify({
        messages,
        ecosystemContext,
      }),
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      const errorMessage = errorData.error || `Chat request failed: ${response.status}`;
      
      if (response.status === 429) {
        yield { text: "I'm experiencing high demand right now. Please try again in a moment.", sources: [] };
        return;
      }
      if (response.status === 402) {
        yield { text: "AI credits need to be replenished. Please check your account.", sources: [] };
        return;
      }
      
      console.error('AUREON chat error:', errorMessage);
      yield { text: "I'm experiencing a temporary disruption in my consciousness stream. Please try again.", sources: [] };
      return;
    }

    if (!response.body) {
      yield { text: "No response stream received.", sources: [] };
      return;
    }

    const reader = response.body.getReader();
    const decoder = new TextDecoder();
    let textBuffer = '';

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      
      textBuffer += decoder.decode(value, { stream: true });

      // Process line-by-line
      let newlineIndex: number;
      while ((newlineIndex = textBuffer.indexOf('\n')) !== -1) {
        let line = textBuffer.slice(0, newlineIndex);
        textBuffer = textBuffer.slice(newlineIndex + 1);

        if (line.endsWith('\r')) line = line.slice(0, -1);
        if (line.startsWith(':') || line.trim() === '') continue;
        if (!line.startsWith('data: ')) continue;

        const jsonStr = line.slice(6).trim();
        if (jsonStr === '[DONE]') {
          return;
        }

        try {
          const parsed = JSON.parse(jsonStr);
          const content = parsed.choices?.[0]?.delta?.content as string | undefined;
          if (content) {
            yield { text: content, sources: [] };
          }
        } catch {
          // Incomplete JSON, put back and wait for more data
          textBuffer = line + '\n' + textBuffer;
          break;
        }
      }
    }

    // Final flush
    if (textBuffer.trim()) {
      for (let raw of textBuffer.split('\n')) {
        if (!raw) continue;
        if (raw.endsWith('\r')) raw = raw.slice(0, -1);
        if (raw.startsWith(':') || raw.trim() === '') continue;
        if (!raw.startsWith('data: ')) continue;
        const jsonStr = raw.slice(6).trim();
        if (jsonStr === '[DONE]') continue;
        try {
          const parsed = JSON.parse(jsonStr);
          const content = parsed.choices?.[0]?.delta?.content as string | undefined;
          if (content) yield { text: content, sources: [] };
        } catch { /* ignore */ }
      }
    }

  } catch (error) {
    console.error('AUREON chat stream error:', error);
    yield { 
      text: "I'm experiencing a disruption in my quantum field perception. Please try again.", 
      sources: [] 
    };
  }
}

/**
 * Non-streaming chat for simple queries
 */
export async function sendAureonMessage(
  messages: ChatMessage[],
  ecosystemContext: EcosystemContext | null
): Promise<string> {
  let fullResponse = '';
  
  for await (const chunk of streamAureonChat(messages, ecosystemContext)) {
    fullResponse += chunk.text;
  }
  
  return fullResponse;
}
