// TypeScript-Pro Agent: Type-safe API client for Grantha backend
import type { 
  AuthRequest, 
  AuthResponse, 
  ChatMessage, 
  ChatSession,
  Model,
  WikiEntry,
  ResearchQuery,
  ResearchResult,
  APIError 
} from '../types/api.js';

const API_BASE_URL = 'http://localhost:8000/api/v1';

class APIClient {
  private baseURL: string;
  private token: string | null = null;

  constructor(baseURL: string = API_BASE_URL) {
    this.baseURL = baseURL;
    
    // Try to get token from localStorage
    if (typeof localStorage !== 'undefined') {
      this.token = localStorage.getItem('grantha_auth_token');
    }
  }

  private getHeaders(): HeadersInit {
    const headers: HeadersInit = {
      'Content-Type': 'application/json',
    };

    if (this.token) {
      headers['Authorization'] = `Bearer ${this.token}`;
    }

    return headers;
  }

  private async request<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
    const url = `${this.baseURL}${endpoint}`;
    
    const response = await fetch(url, {
      ...options,
      headers: {
        ...this.getHeaders(),
        ...options.headers,
      },
    });

    if (!response.ok) {
      const errorData: APIError = await response.json().catch(() => ({
        error: `HTTP ${response.status}`,
        message: response.statusText,
        code: response.status
      }));
      
      throw new Error(errorData.message || `HTTP ${response.status}: ${response.statusText}`);
    }

    return response.json();
  }

  // Authentication methods
  async login(credentials: AuthRequest): Promise<AuthResponse> {
    const response = await this.request<AuthResponse>('/auth/login', {
      method: 'POST',
      body: JSON.stringify(credentials),
    });

    this.token = response.access_token;
    if (typeof localStorage !== 'undefined') {
      localStorage.setItem('grantha_auth_token', response.access_token);
    }

    return response;
  }

  async register(credentials: AuthRequest): Promise<AuthResponse> {
    const response = await this.request<AuthResponse>('/auth/register', {
      method: 'POST',
      body: JSON.stringify(credentials),
    });

    this.token = response.access_token;
    if (typeof localStorage !== 'undefined') {
      localStorage.setItem('grantha_auth_token', response.access_token);
    }

    return response;
  }

  async logout(): Promise<void> {
    await this.request('/auth/logout', { method: 'POST' });
    this.token = null;
    if (typeof localStorage !== 'undefined') {
      localStorage.removeItem('grantha_auth_token');
    }
  }

  // Chat methods
  async getChatSessions(): Promise<ChatSession[]> {
    return this.request<ChatSession[]>('/chat/sessions');
  }

  async createChatSession(title?: string): Promise<ChatSession> {
    return this.request<ChatSession>('/chat/sessions', {
      method: 'POST',
      body: JSON.stringify({ title }),
    });
  }

  async getChatMessages(sessionId: string): Promise<ChatMessage[]> {
    return this.request<ChatMessage[]>(`/chat/sessions/${sessionId}/messages`);
  }

  async sendChatMessage(sessionId: string, content: string): Promise<ChatMessage> {
    return this.request<ChatMessage>(`/chat/sessions/${sessionId}/messages`, {
      method: 'POST',
      body: JSON.stringify({ content }),
    });
  }

  // Models methods
  async getModels(): Promise<Model[]> {
    return this.request<Model[]>('/models');
  }

  async getModel(modelId: string): Promise<Model> {
    return this.request<Model>(`/models/${modelId}`);
  }

  // Wiki methods
  async getWikiEntries(): Promise<WikiEntry[]> {
    return this.request<WikiEntry[]>('/wiki');
  }

  async createWikiEntry(entry: Omit<WikiEntry, 'id' | 'created_at' | 'updated_at'>): Promise<WikiEntry> {
    return this.request<WikiEntry>('/wiki', {
      method: 'POST',
      body: JSON.stringify(entry),
    });
  }

  async updateWikiEntry(id: string, entry: Partial<WikiEntry>): Promise<WikiEntry> {
    return this.request<WikiEntry>(`/wiki/${id}`, {
      method: 'PUT',
      body: JSON.stringify(entry),
    });
  }

  async deleteWikiEntry(id: string): Promise<void> {
    await this.request(`/wiki/${id}`, { method: 'DELETE' });
  }

  // Research methods
  async submitResearchQuery(query: ResearchQuery): Promise<ResearchResult> {
    return this.request<ResearchResult>('/research/query', {
      method: 'POST',
      body: JSON.stringify(query),
    });
  }

  async getResearchHistory(): Promise<ResearchResult[]> {
    return this.request<ResearchResult[]>('/research/history');
  }

  // Additional auth methods
  async getAuthStatus(): Promise<{ auth_required: boolean }> {
    return this.request<{ auth_required: boolean }>('/auth/status');
  }

  async validateAuthCode(config: { code: string }): Promise<{ success: boolean }> {
    return this.request<{ success: boolean }>('/auth/validate', {
      method: 'POST',
      body: JSON.stringify(config),
    });
  }

  // Model configuration methods
  async getModelConfig(): Promise<any> {
    return this.request('/models/config');
  }

  // Chat completion method
  async chatCompletion(request: any): Promise<any> {
    return this.request('/chat/completion', {
      method: 'POST',
      body: JSON.stringify(request),
    });
  }

  // Simple chat methods
  async simpleChat(request: any): Promise<any> {
    return this.request('/simple/chat', {
      method: 'POST',
      body: JSON.stringify(request),
    });
  }

  async simpleRAG(request: any): Promise<any> {
    return this.request('/simple/rag', {
      method: 'POST',
      body: JSON.stringify(request),
    });
  }

  // Health check
  async healthCheck(): Promise<{ status: string }> {
    return this.request<{ status: string }>('/health');
  }
}

export const apiClient = new APIClient();
export default APIClient;