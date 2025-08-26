/**
 * Deepwiki Integration Utilities
 * Provides compatibility layer and feature integration
 */

import type {
  UnifiedChatMessage,
  ChatCompletionRequest,
  ChatStreamData,
  UnifiedWebSocketMessage,
  WikiPageExtended,
  UnifiedAPIError
} from '../types/shared.js';
import { wsClient } from '../websocket/client.js';

// Environment configuration
const SERVER_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

/**
 * Convert HTTP URL to WebSocket URL
 */
export const getWebSocketUrl = (endpoint: string = '/ws/chat'): string => {
  const baseUrl = SERVER_BASE_URL;
  const wsBaseUrl = baseUrl.replace(/^http/, 'ws');
  return `${wsBaseUrl}${endpoint}`;
};

/**
 * Enhanced WebSocket client wrapper for deepwiki compatibility
 */
export class DeepwikiWebSocketClient {
  private ws: WebSocket | null = null;
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 5;
  private reconnectInterval = 3000;
  
  constructor() {
    // Use existing Grantha WebSocket client when possible
    this.initializeFromGrantha();
  }

  private initializeFromGrantha() {
    // Leverage existing Grantha WebSocket infrastructure
    wsClient.onChatStream((message) => {
      this.handleStreamMessage(message);
    });
  }

  /**
   * Create a WebSocket connection compatible with deepwiki patterns
   */
  connect(
    request: ChatCompletionRequest,
    onMessage: (data: ChatStreamData) => void,
    onError?: (error: Event | UnifiedAPIError) => void,
    onClose?: () => void
  ): WebSocket {
    const wsUrl = getWebSocketUrl();
    
    // Close existing connection if any
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.close();
    }

    this.ws = new WebSocket(wsUrl);

    this.ws.onopen = () => {
      console.log('Deepwiki-compatible WebSocket connection established');
      this.reconnectAttempts = 0;
      
      // Send the initial request
      this.ws?.send(JSON.stringify({
        type: 'chat_completion',
        data: request
      }));
    };

    this.ws.onmessage = (event) => {
      try {
        let data: any;
        
        // Handle both string and JSON responses
        if (typeof event.data === 'string') {
          try {
            data = JSON.parse(event.data);
          } catch {
            // Plain text message
            data = {
              session_id: 'default',
              content: event.data,
              done: false
            };
          }
        }

        // Convert to ChatStreamData format
        const streamData: ChatStreamData = this.normalizeStreamData(data);
        onMessage(streamData);

      } catch (error) {
        console.error('Failed to process WebSocket message:', error);
        if (onError) {
          onError(new Event('MessageProcessingError'));
        }
      }
    };

    this.ws.onerror = (error) => {
      console.error('WebSocket error:', error);
      if (onError) onError(error);
    };

    this.ws.onclose = () => {
      console.log('WebSocket connection closed');
      if (onClose) onClose();
      
      // Attempt reconnection if not at max attempts
      if (this.reconnectAttempts < this.maxReconnectAttempts) {
        this.scheduleReconnect(request, onMessage, onError, onClose);
      }
    };

    return this.ws;
  }

  private scheduleReconnect(
    request: ChatCompletionRequest,
    onMessage: (data: ChatStreamData) => void,
    onError?: (error: Event | UnifiedAPIError) => void,
    onClose?: () => void
  ) {
    this.reconnectAttempts++;
    console.log(`Attempting reconnect ${this.reconnectAttempts}/${this.maxReconnectAttempts}`);
    
    setTimeout(() => {
      this.connect(request, onMessage, onError, onClose);
    }, this.reconnectInterval * this.reconnectAttempts);
  }

  private normalizeStreamData(data: any): ChatStreamData {
    // Handle various data formats
    if (data.type === 'chat_stream' && data.data) {
      return data.data as ChatStreamData;
    }
    
    // Direct ChatStreamData format
    if ('session_id' in data && 'done' in data) {
      return data as ChatStreamData;
    }
    
    // Convert other formats
    return {
      session_id: data.session_id || data.id || 'default',
      content: data.content || data.message || data.text || '',
      done: data.done || data.finished || false,
      model: data.model,
      provider: data.provider,
      usage: data.usage,
      error: data.error
    };
  }

  private handleStreamMessage(message: any) {
    // Process stream messages from Grantha WebSocket
    console.log('Stream message received:', message);
  }

  /**
   * Close the WebSocket connection
   */
  close(): void {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.close();
      this.ws = null;
    }
  }

  /**
   * Send a message through the WebSocket
   */
  send(message: any): void {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(message));
    } else {
      console.warn('WebSocket is not connected');
    }
  }
}

/**
 * Repository URL utilities from deepwiki
 */
export function getRepoUrl(url: string): string {
  // Extract clean repository URL from various formats
  const patterns = [
    /github\.com[:/]([^/]+\/[^/.]+)/,
    /gitlab\.com[:/]([^/]+\/[^/.]+)/,
    /bitbucket\.org[:/]([^/]+\/[^/.]+)/
  ];

  for (const pattern of patterns) {
    const match = url.match(pattern);
    if (match) {
      return `https://github.com/${match[1]}`;
    }
  }

  return url;
}

/**
 * URL decoder utility from deepwiki
 */
export function urlDecoder(encodedUrl: string): string {
  try {
    return decodeURIComponent(encodedUrl);
  } catch {
    return encodedUrl;
  }
}

/**
 * Convert between message formats
 */
export function convertToUnifiedMessage(message: any): UnifiedChatMessage {
  return {
    role: message.role || 'user',
    content: message.content || message.text || '',
    timestamp: message.timestamp || Date.now(),
    id: message.id,
    metadata: message.metadata
  };
}

/**
 * Format wiki page for display
 */
export function formatWikiPage(page: WikiPageExtended): string {
  const sections = [];
  
  sections.push(`# ${page.title}\n`);
  
  if (page.importance) {
    sections.push(`**Importance:** ${page.importance}\n`);
  }
  
  sections.push(page.content);
  
  if (page.filePaths && page.filePaths.length > 0) {
    sections.push('\n## Related Files\n');
    page.filePaths.forEach(path => {
      sections.push(`- ${path}`);
    });
  }
  
  if (page.relatedPages && page.relatedPages.length > 0) {
    sections.push('\n## Related Pages\n');
    page.relatedPages.forEach(pageId => {
      sections.push(`- [[${pageId}]]`);
    });
  }
  
  return sections.join('\n');
}

/**
 * Create a unified API client that works with both systems
 */
export class UnifiedAPIClient {
  private baseUrl: string;
  
  constructor(baseUrl: string = SERVER_BASE_URL) {
    this.baseUrl = baseUrl;
  }
  
  async request<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
    const url = `${this.baseUrl}${endpoint}`;
    
    const defaultHeaders = {
      'Content-Type': 'application/json',
    };
    
    const response = await fetch(url, {
      ...options,
      headers: {
        ...defaultHeaders,
        ...options.headers,
      },
    });
    
    if (!response.ok) {
      const error: UnifiedAPIError = {
        message: `API request failed: ${response.statusText}`,
        code: response.status,
        type: response.status >= 500 ? 'server_error' : 'client_error'
      };
      
      try {
        const errorData = await response.json();
        error.details = errorData;
        error.message = errorData.message || error.message;
      } catch {
        // Response is not JSON
      }
      
      throw error;
    }
    
    return response.json();
  }
  
  // Chat completion with streaming support
  async chatCompletion(request: ChatCompletionRequest): Promise<WebSocket> {
    const client = new DeepwikiWebSocketClient();
    return client.connect(
      request,
      (data) => console.log('Stream data:', data),
      (error) => console.error('Stream error:', error),
      () => console.log('Stream closed')
    );
  }
  
  // Get model configuration
  async getModelConfig() {
    return this.request('/models/config');
  }
  
  // Wiki generation
  async generateWiki(params: any) {
    return this.request('/wiki/generate', {
      method: 'POST',
      body: JSON.stringify(params)
    });
  }
}

// Export singleton instances
export const deepwikiClient = new DeepwikiWebSocketClient();
export const unifiedAPI = new UnifiedAPIClient();