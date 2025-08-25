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

const API_BASE_URL = 'http://localhost:8001';

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
  async getAuthStatus(): Promise<{ auth_required: boolean }> {
    return this.request<{ auth_required: boolean }>('/auth/status');
  }

  async validateAuthCode(config: { code: string }): Promise<{ success: boolean }> {
    return this.request<{ success: boolean }>('/auth/validate', {
      method: 'POST',
      body: JSON.stringify(config),
    });
  }

  async getLanguageConfig(): Promise<any> {
    return this.request('/auth/lang/config');
  }

  // Legacy methods for compatibility - implement as needed
  async login(credentials: AuthRequest): Promise<AuthResponse> {
    // Note: Backend doesn't have login endpoint, implement based on auth flow
    throw new Error('Login endpoint not implemented in backend API');
  }

  async register(credentials: AuthRequest): Promise<AuthResponse> {
    // Note: Backend doesn't have register endpoint, implement based on auth flow
    throw new Error('Register endpoint not implemented in backend API');
  }

  async logout(): Promise<void> {
    this.token = null;
    if (typeof localStorage !== 'undefined') {
      localStorage.removeItem('grantha_auth_token');
    }
  }

  // Chat methods - Updated to match backend API
  async chatCompletion(request: {
    messages: any[];
    model?: string;
    provider?: string;
    stream?: boolean;
    temperature?: number;
    max_tokens?: number;
  }): Promise<any> {
    return this.request('/chat/completion', {
      method: 'POST',
      body: JSON.stringify(request),
    });
  }

  // Legacy methods for compatibility - not implemented in backend
  async getChatSessions(): Promise<ChatSession[]> {
    throw new Error('Chat sessions endpoint not implemented in backend API');
  }

  async createChatSession(title?: string): Promise<ChatSession> {
    throw new Error('Create chat session endpoint not implemented in backend API');
  }

  async getChatMessages(sessionId: string): Promise<ChatMessage[]> {
    throw new Error('Chat messages endpoint not implemented in backend API');
  }

  async sendChatMessage(sessionId: string, content: string): Promise<ChatMessage> {
    throw new Error('Send chat message endpoint not implemented in backend API');
  }

  // Models methods - Updated to match backend API
  async getModelConfig(): Promise<any> {
    return this.request('/models/config');
  }

  // Legacy model methods - not implemented in backend
  async getModels(): Promise<Model[]> {
    throw new Error('Individual models endpoint not implemented in backend API. Use getModelConfig() instead.');
  }

  async getModel(modelId: string): Promise<Model> {
    throw new Error('Single model endpoint not implemented in backend API. Use getModelConfig() instead.');
  }

  // Wiki methods - Updated to match backend API
  async generateWiki(request: {
    repo_url: string;
    language?: string;
    provider?: string;
    model?: string;
    token?: string;
    repo_type?: string;
  }): Promise<any> {
    return this.request('/wiki/generate', {
      method: 'POST',
      body: JSON.stringify(request),
    });
  }

  async saveWikiCache(request: {
    repo: any;
    language: string;
    wiki_structure: any;
    generated_pages: Record<string, any>;
    provider: string;
    model: string;
  }): Promise<any> {
    return this.request('/wiki/cache', {
      method: 'POST',
      body: JSON.stringify(request),
    });
  }

  async exportWiki(request: {
    repo_url: string;
    pages: any[];
    format: 'markdown' | 'json';
  }): Promise<any> {
    return this.request('/wiki/export', {
      method: 'POST',
      body: JSON.stringify(request),
    });
  }

  // Legacy wiki methods - not implemented in backend
  async getWikiEntries(): Promise<WikiEntry[]> {
    throw new Error('Wiki entries list endpoint not implemented in backend API. Use generateWiki() instead.');
  }

  async createWikiEntry(entry: Omit<WikiEntry, 'id' | 'created_at' | 'updated_at'>): Promise<WikiEntry> {
    throw new Error('Create wiki entry endpoint not implemented in backend API. Use generateWiki() instead.');
  }

  async updateWikiEntry(id: string, entry: Partial<WikiEntry>): Promise<WikiEntry> {
    throw new Error('Update wiki entry endpoint not implemented in backend API.');
  }

  async deleteWikiEntry(id: string): Promise<void> {
    throw new Error('Delete wiki entry endpoint not implemented in backend API.');
  }

  // Research methods - Updated to match backend API
  async deepResearch(request: {
    query: string;
    repo_url: string;
    language?: string;
    provider?: string;
    model?: string;
    token?: string;
    repo_type?: string;
  }): Promise<any> {
    return this.request('/research/deep', {
      method: 'POST',
      body: JSON.stringify(request),
    });
  }

  // Legacy research methods - not implemented in backend
  async submitResearchQuery(query: ResearchQuery): Promise<ResearchResult> {
    throw new Error('Research query endpoint not implemented in backend API. Use deepResearch() instead.');
  }

  async getResearchHistory(): Promise<ResearchResult[]> {
    throw new Error('Research history endpoint not implemented in backend API.');
  }

  // Simple methods - Updated to match backend API
  async simpleChat(request: {
    user_query: string;
    repo_url?: string;
    provider?: string;
    model?: string;
    language?: string;
    token?: string;
    repo_type?: string;
  }): Promise<any> {
    return this.request('/simple/chat', {
      method: 'POST',
      body: JSON.stringify(request),
    });
  }

  async simpleRAG(request: {
    query: string;
    repo_url: string;
    provider?: string;
    model?: string;
    language?: string;
    token?: string;
    repo_type?: string;
    k?: number;
  }): Promise<any> {
    return this.request('/simple/rag', {
      method: 'POST',
      body: JSON.stringify(request),
    });
  }

  // Root and health endpoints
  async root(): Promise<any> {
    return this.request('/');
  }

  async healthCheck(): Promise<any> {
    return this.request('/health');
  }
}

export const apiClient = new APIClient();
export default APIClient;