import type { AxiosRequestConfig } from 'axios';
import { request } from './request';

// Types
export interface ChatMessage {
  role: 'system' | 'user' | 'assistant';
  content: string;
}

export interface ChatCompletionRequest {
  model: string;
  messages: ChatMessage[];
  stream?: boolean;
  temperature?: number;
  max_tokens?: number;
  top_p?: number;
}

export interface ChatCompletionResponse {
  id: string;
  object: string;
  created: number;
  model: string;
  choices: {
    index: number;
    message: ChatMessage;
    finish_reason: string;
  }[];
  usage: {
    prompt_tokens: number;
    completion_tokens: number;
    total_tokens: number;
  };
}

export interface ChatCompletionChunk {
  id: string;
  object: string;
  created: number;
  model: string;
  choices: {
    index: number;
    delta: {
      role?: string;
      content?: string;
    };
    finish_reason: string | null;
  }[];
}

export interface ModelInfo {
  id: string;
  object: string;
  owned_by: string;
}

export interface ModelsResponse {
  object: string;
  data: ModelInfo[];
}

// Get available models
export function getAvailableModels(): Promise<ModelsResponse> {
  return request({
    url: '/proxy/api/v1/models',
    method: 'get',
  });
}

// Send non-streaming chat message
export async function sendChatMessage(
  data: ChatCompletionRequest,
  apiKey: string
): Promise<ChatCompletionResponse> {
  const config: AxiosRequestConfig = {
    url: '/proxy/api/v1/chat/completions',
    method: 'post',
    data,
    headers: {
      'Authorization': `Bearer ${apiKey}`,
    },
  };
  return request(config);
}

// Send streaming chat message
export async function sendChatMessageStream(
  data: ChatCompletionRequest,
  apiKey: string,
  onChunk: (chunk: string, done?: boolean) => void
): Promise<void> {
  const streamData = { ...data, stream: true };
  
  try {
    const response = await fetch('/proxy/api/v1/chat/completions', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${apiKey}`,
      },
      body: JSON.stringify(streamData),
    });

    if (!response.ok) {
      const errorText = await response.text();
      throw new Error(`HTTP ${response.status}: ${errorText}`);
    }

    const reader = response.body?.getReader();
    if (!reader) {
      throw new Error('No response body');
    }

    const decoder = new TextDecoder();
    let buffer = '';

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      buffer += decoder.decode(value, { stream: true });
      const lines = buffer.split('\n');
      buffer = lines.pop() || '';

      for (const line of lines) {
        const trimmedLine = line.trim();
        if (!trimmedLine || trimmedLine === 'data: [DONE]') {
          if (trimmedLine === 'data: [DONE]') {
            onChunk('', true);
            return;
          }
          continue;
        }

        if (trimmedLine.startsWith('data: ')) {
          try {
            const jsonData = JSON.parse(trimmedLine.slice(6));
            const content = jsonData.choices?.[0]?.delta?.content;
            if (content) {
              onChunk(content, false);
            }
          } catch {
            // Skip invalid JSON
          }
        }
      }
    }

    // Process any remaining buffer
    if (buffer.trim()) {
      const trimmedLine = buffer.trim();
      if (trimmedLine.startsWith('data: ') && trimmedLine !== 'data: [DONE]') {
        try {
          const jsonData = JSON.parse(trimmedLine.slice(6));
          const content = jsonData.choices?.[0]?.delta?.content;
          if (content) {
            onChunk(content, false);
          }
        } catch {
          // Skip invalid JSON
        }
      }
    }

    onChunk('', true);
  } catch (error) {
    throw error;
  }
}
