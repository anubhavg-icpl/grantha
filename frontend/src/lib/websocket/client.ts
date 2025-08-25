// WebSocket-Engineer Agent: Real-time WebSocket client for live chat streaming
import { writable } from 'svelte/store';
import type { ChatStreamMessage, WebSocketMessage } from '../types/api.js';

export type WebSocketStatus = 'connecting' | 'connected' | 'disconnected' | 'error';

interface WebSocketClientConfig {
  url?: string;
  reconnectInterval?: number;
  maxReconnectAttempts?: number;
  heartbeatInterval?: number;
}

class WebSocketClient {
  private ws: WebSocket | null = null;
  private url: string;
  private reconnectInterval: number;
  private maxReconnectAttempts: number;
  private heartbeatInterval: number;
  private reconnectAttempts = 0;
  private heartbeatTimer: NodeJS.Timeout | null = null;
  private reconnectTimer: NodeJS.Timeout | null = null;

  // Stores for reactive state management
  public status = writable<WebSocketStatus>('disconnected');
  public messages = writable<WebSocketMessage[]>([]);
  public error = writable<string | null>(null);

  constructor(config: WebSocketClientConfig = {}) {
    this.url = config.url || 'ws://localhost:8000/ws';
    this.reconnectInterval = config.reconnectInterval || 3000;
    this.maxReconnectAttempts = config.maxReconnectAttempts || 5;
    this.heartbeatInterval = config.heartbeatInterval || 30000;
  }

  connect(token?: string): void {
    if (this.ws && (this.ws.readyState === WebSocket.CONNECTING || this.ws.readyState === WebSocket.OPEN)) {
      return;
    }

    this.status.set('connecting');
    this.error.set(null);

    const wsUrl = token ? `${this.url}?token=${token}` : this.url;
    this.ws = new WebSocket(wsUrl);

    this.ws.onopen = () => {
      console.log('WebSocket connected');
      this.status.set('connected');
      this.reconnectAttempts = 0;
      this.startHeartbeat();
    };

    this.ws.onmessage = (event) => {
      try {
        const message: WebSocketMessage = JSON.parse(event.data);
        this.messages.update(messages => [...messages, message]);

        // Handle specific message types
        if (message.type === 'error') {
          this.error.set(message.data.message || 'Unknown WebSocket error');
        }
      } catch (err) {
        console.error('Failed to parse WebSocket message:', err);
        this.error.set('Failed to parse message from server');
      }
    };

    this.ws.onclose = (event) => {
      console.log('WebSocket disconnected:', event.code, event.reason);
      this.status.set('disconnected');
      this.stopHeartbeat();

      if (!event.wasClean && this.reconnectAttempts < this.maxReconnectAttempts) {
        this.scheduleReconnect();
      }
    };

    this.ws.onerror = (event) => {
      console.error('WebSocket error:', event);
      this.status.set('error');
      this.error.set('WebSocket connection error');
    };
  }

  disconnect(): void {
    this.stopHeartbeat();
    if (this.reconnectTimer) {
      clearTimeout(this.reconnectTimer);
      this.reconnectTimer = null;
    }

    if (this.ws) {
      this.ws.close(1000, 'Client disconnect');
      this.ws = null;
    }

    this.status.set('disconnected');
  }

  send(message: any): void {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(message));
    } else {
      console.warn('WebSocket is not connected. Message not sent:', message);
      this.error.set('Cannot send message: WebSocket not connected');
    }
  }

  // Chat-specific methods
  sendChatMessage(sessionId: string, content: string): void {
    this.send({
      type: 'chat_message',
      data: {
        session_id: sessionId,
        content: content,
        timestamp: Date.now()
      }
    });
  }

  joinChatSession(sessionId: string): void {
    this.send({
      type: 'join_session',
      data: { session_id: sessionId }
    });
  }

  leaveChatSession(sessionId: string): void {
    this.send({
      type: 'leave_session',
      data: { session_id: sessionId }
    });
  }

  // Subscribe to specific message types
  onChatStream(callback: (message: ChatStreamMessage) => void): () => void {
    const unsubscribe = this.messages.subscribe(messages => {
      const latestMessage = messages[messages.length - 1];
      if (latestMessage && latestMessage.type === 'chat_stream') {
        callback(latestMessage as ChatStreamMessage);
      }
    });

    return unsubscribe;
  }

  private startHeartbeat(): void {
    this.heartbeatTimer = setInterval(() => {
      if (this.ws && this.ws.readyState === WebSocket.OPEN) {
        this.send({ type: 'ping', timestamp: Date.now() });
      }
    }, this.heartbeatInterval);
  }

  private stopHeartbeat(): void {
    if (this.heartbeatTimer) {
      clearInterval(this.heartbeatTimer);
      this.heartbeatTimer = null;
    }
  }

  private scheduleReconnect(): void {
    this.reconnectAttempts++;
    console.log(`Attempting to reconnect (${this.reconnectAttempts}/${this.maxReconnectAttempts})`);

    this.reconnectTimer = setTimeout(() => {
      this.connect();
    }, this.reconnectInterval * this.reconnectAttempts);
  }

  // Clear message history
  clearMessages(): void {
    this.messages.set([]);
  }

  // Get current status
  getStatus(): WebSocketStatus {
    let currentStatus: WebSocketStatus = 'disconnected';
    this.status.subscribe(status => currentStatus = status)();
    return currentStatus;
  }
}

// Global WebSocket client instance
export const wsClient = new WebSocketClient();

// Utility function to initialize WebSocket with auth token
export async function initializeWebSocket(): Promise<void> {
  const token = typeof localStorage !== 'undefined' ?
    localStorage.getItem('grantha_auth_token') : null;

  if (token) {
    wsClient.connect(token);
  }
}

export default WebSocketClient;
