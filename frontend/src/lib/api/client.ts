// TypeScript-Pro Agent: Type-safe API client for Grantha backend
import type {
  AuthRequest,
  AuthResponse,
  ChatMessage,
  ChatResponse,
  ChatSession,
  Model,
  ModelConfig,
  WikiEntry,
  WikiPage,
  WikiStructureModel,
  RepoInfo,
  ResearchQuery,
  ResearchResult,
  APIError,
  ProcessedProjectEntry,
} from "../types/api.js";

const API_BASE_URL = ""; // Use relative URLs to leverage Vite proxy

class APIClient {
  private baseURL: string;
  private token: string | null = null;

  constructor(baseURL: string = API_BASE_URL) {
    // In development, use empty string for relative URLs
    // In production, this can be overridden with actual API URL
    this.baseURL = baseURL || "";

    // Try to get token from localStorage (JWT token storage)
    if (typeof localStorage !== "undefined") {
      const storedTokens = localStorage.getItem("grantha-tokens");
      if (storedTokens) {
        try {
          const tokenData = JSON.parse(storedTokens);
          this.token = tokenData.access_token;
        } catch (error) {
          console.error("Failed to parse stored tokens:", error);
          // Fallback to legacy token storage
          this.token = localStorage.getItem("grantha_auth_token");
        }
      } else {
        // Fallback to legacy token storage
        this.token = localStorage.getItem("grantha_auth_token");
      }
    }
  }

  // Token management methods
  setToken(token: string): void {
    this.token = token;
  }

  clearToken(): void {
    this.token = null;
  }

  getToken(): string | null {
    return this.token;
  }

  private getHeaders(): HeadersInit {
    const headers: HeadersInit = {
      "Content-Type": "application/json",
    };

    if (this.token) {
      headers["Authorization"] = `Bearer ${this.token}`;
    }

    return headers;
  }

  async request<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
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
        code: response.status,
      }));

      throw new Error(
        errorData.message || `HTTP ${response.status}: ${response.statusText}`,
      );
    }

    return response.json();
  }

  // Authentication methods
  async getAuthStatus(): Promise<{ auth_required: boolean }> {
    // Try v2 API first, fallback to v1
    try {
      return await this.request<{ auth_required: boolean }>("/auth/v2/status");
    } catch (error) {
      return await this.request<{ auth_required: boolean }>("/auth/status");
    }
  }

  async validateAuthCode(config: {
    code: string;
  }): Promise<{ success: boolean }> {
    return this.request<{ success: boolean }>("/auth/validate", {
      method: "POST",
      body: JSON.stringify(config),
    });
  }

  async getLanguageConfig(): Promise<any> {
    return this.request("/auth/lang/config");
  }

  // V2 Authentication methods
  async registerUser(userData: {
    username: string;
    password: string;
    email?: string;
    full_name?: string;
    bio?: string;
  }): Promise<any> {
    return this.request("/auth/v2/register", {
      method: "POST",
      body: JSON.stringify(userData),
    });
  }

  async loginUser(credentials: {
    username: string;
    password: string;
    remember_me?: boolean;
  }): Promise<any> {
    return this.request("/auth/v2/login", {
      method: "POST",
      body: JSON.stringify(credentials),
    });
  }

  async refreshAccessToken(refreshToken: string): Promise<any> {
    return this.request("/auth/v2/refresh", {
      method: "POST",
      body: JSON.stringify({ refresh_token: refreshToken }),
    });
  }

  async logoutUser(logoutData?: {
    refresh_token?: string;
    revoke_all?: boolean;
  }): Promise<any> {
    return this.request("/auth/v2/logout", {
      method: "POST",
      body: JSON.stringify(logoutData || {}),
    });
  }

  async getCurrentUser(): Promise<any> {
    return this.request("/auth/v2/me");
  }

  async updateCurrentUser(updateData: any): Promise<any> {
    return this.request("/auth/v2/me", {
      method: "PUT",
      body: JSON.stringify(updateData),
    });
  }

  async changePassword(passwordData: {
    current_password: string;
    new_password: string;
  }): Promise<any> {
    return this.request("/auth/v2/change-password", {
      method: "POST",
      body: JSON.stringify(passwordData),
    });
  }

  async getUserSessions(): Promise<any> {
    return this.request("/auth/v2/sessions");
  }

  async revokeSession(sessionId: string): Promise<any> {
    return this.request(`/auth/v2/sessions/${sessionId}`, {
      method: "DELETE",
    });
  }

  async getTokenInfo(): Promise<any> {
    return this.request("/auth/v2/token/info");
  }

  // Legacy methods for compatibility
  async login(credentials: AuthRequest): Promise<AuthResponse> {
    try {
      const response = await this.loginUser({
        username: credentials.username,
        password: credentials.password,
      });
      
      return {
        access_token: response.access_token,
        token_type: "Bearer",
        user: {
          id: response.user_id,
          username: response.username,
          email: response.email,
        },
      };
    } catch (error) {
      throw new Error("Login failed");
    }
  }

  async register(credentials: AuthRequest): Promise<AuthResponse> {
    try {
      const response = await this.registerUser({
        username: credentials.username,
        password: credentials.password,
      });
      
      return {
        access_token: "", // Registration doesn't return token
        token_type: "Bearer",
        user: {
          id: response.id,
          username: response.username,
          email: response.email,
        },
      };
    } catch (error) {
      throw new Error("Registration failed");
    }
  }

  async logout(): Promise<void> {
    try {
      await this.logoutUser();
    } catch (error) {
      console.warn("Logout API call failed:", error);
    }
    
    this.token = null;
    if (typeof localStorage !== "undefined") {
      localStorage.removeItem("grantha_auth_token");
      localStorage.removeItem("grantha-tokens");
    }
  }

  // Chat methods - Updated to match backend API
  async chatCompletion(request: {
    messages: ChatMessage[];
    model?: string;
    provider?: string;
    stream?: boolean;
    temperature?: number;
    max_tokens?: number;
  }): Promise<ChatResponse> {
    const response = await this.request("/chat/completion", {
      method: "POST",
      body: JSON.stringify(request),
    });

    // Ensure consistent response format
    const typedResponse = response as ChatResponse & { message?: string };
    return {
      content:
        typedResponse.content ||
        typedResponse.message ||
        "No response received",
      model: typedResponse.model || "unknown",
      provider: typedResponse.provider || "unknown",
      usage: typedResponse.usage,
      finish_reason: typedResponse.finish_reason,
    };
  }

  // Streaming chat completion using Server-Sent Events
  async chatCompletionStream(request: {
    messages: any[];
    model?: string;
    provider?: string;
    temperature?: number;
    max_tokens?: number;
  }): Promise<ReadableStream<Uint8Array>> {
    const url = `${this.baseURL}/chat/completions/stream`;

    const response = await fetch(url, {
      method: "POST",
      headers: {
        ...this.getHeaders(),
        Accept: "text/event-stream",
        "Cache-Control": "no-cache",
      },
      body: JSON.stringify({
        ...request,
        stream: true,
      }),
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({
        error: `HTTP ${response.status}`,
        message: response.statusText,
        code: response.status,
      }));

      throw new Error(
        errorData.message || `HTTP ${response.status}: ${response.statusText}`,
      );
    }

    if (!response.body) {
      throw new Error("No response body received from streaming endpoint");
    }

    return response.body;
  }

  // Legacy methods for compatibility - not implemented in backend
  async getChatSessions(): Promise<ChatSession[]> {
    throw new Error("Chat sessions endpoint not implemented in backend API");
  }

  async createChatSession(title?: string): Promise<ChatSession> {
    throw new Error(
      "Create chat session endpoint not implemented in backend API",
    );
  }

  async getChatMessages(sessionId: string): Promise<ChatMessage[]> {
    throw new Error("Chat messages endpoint not implemented in backend API");
  }

  async sendChatMessage(
    sessionId: string,
    content: string,
  ): Promise<ChatMessage> {
    throw new Error(
      "Send chat message endpoint not implemented in backend API",
    );
  }

  // Models methods - Updated to match backend API
  async getModelConfig(): Promise<ModelConfig> {
    return this.request("/models/config");
  }

  // Legacy model methods - deprecated, use getModelConfig() instead
  async getModels(): Promise<Model[]> {
    // Extract models from provider config for backward compatibility
    const config = await this.getModelConfig();
    return config.providers.flatMap((provider) => provider.models);
  }

  async getModel(modelId: string): Promise<Model> {
    // Extract specific model from provider config for backward compatibility
    const config = await this.getModelConfig();
    const model = config.providers
      .flatMap((provider) => provider.models)
      .find((m) => m.id === modelId);

    if (!model) {
      throw new Error(`Model ${modelId} not found`);
    }

    return model;
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
    const response = await this.request("/wiki/generate", {
      method: "POST",
      body: JSON.stringify(request),
    });

    // Normalize response format
    const typedResponse = response as any;
    return {
      status: typedResponse.status || "success",
      wiki_structure: typedResponse.wiki_structure || typedResponse,
      provider: typedResponse.provider,
      model: typedResponse.model,
      message: typedResponse.message,
      error: typedResponse.error,
    };
  }

  async saveWikiCache(request: {
    repo: any;
    language: string;
    wiki_structure: any;
    generated_pages: Record<string, any>;
    provider: string;
    model: string;
  }): Promise<any> {
    return this.request("/wiki/cache", {
      method: "POST",
      body: JSON.stringify(request),
    });
  }

  async exportWiki(request: {
    repo_url: string;
    pages: any[];
    format: "markdown" | "json";
  }): Promise<any> {
    return this.request("/wiki/export", {
      method: "POST",
      body: JSON.stringify(request),
    });
  }

  // Wiki cache retrieval method - matches OpenAPI spec
  async getWikiCache(params: {
    owner: string;
    repo: string;
    repo_type?: string;
    language?: string;
  }): Promise<any> {
    const searchParams = new URLSearchParams({
      owner: params.owner,
      repo: params.repo,
      repo_type: params.repo_type || "github",
      language: params.language || "en",
    });

    return this.request(`/wiki/cache?${searchParams}`);
  }

  // Legacy wiki methods - deprecated, use specific wiki endpoints instead
  async getWikiEntries(): Promise<WikiEntry[]> {
    // Use the new wiki projects endpoint for backward compatibility
    const projects = await this.getWikiProjects();
    return projects.map((project) => ({
      id: project.id,
      title: project.name,
      content: `Wiki for ${project.name}`,
      created_at: project.submittedAt,
      updated_at: project.submittedAt,
      tags: [project.repo_type, project.language],
    }));
  }

  async createWikiEntry(
    entry: Omit<WikiEntry, "id" | "created_at" | "updated_at">,
  ): Promise<WikiEntry> {
    throw new Error(
      "Create wiki entry endpoint not implemented in backend API. Use generateWiki() instead.",
    );
  }

  async updateWikiEntry(
    id: string,
    entry: Partial<WikiEntry>,
  ): Promise<WikiEntry> {
    throw new Error(
      "Update wiki entry endpoint not implemented in backend API.",
    );
  }

  async deleteWikiEntry(id: string): Promise<void> {
    throw new Error(
      "Delete wiki entry endpoint not implemented in backend API.",
    );
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
    return this.request("/research/deep", {
      method: "POST",
      body: JSON.stringify(request),
    });
  }

  // Legacy research methods - not implemented in backend
  async submitResearchQuery(query: ResearchQuery): Promise<ResearchResult> {
    throw new Error(
      "Research query endpoint not implemented in backend API. Use deepResearch() instead.",
    );
  }

  async getResearchHistory(): Promise<ResearchResult[]> {
    throw new Error(
      "Research history endpoint not implemented in backend API.",
    );
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
    const response = await this.request("/simple/chat", {
      method: "POST",
      body: JSON.stringify(request),
    });

    // Normalize response format
    const typedResponse = response as any;
    return {
      message:
        typedResponse.message ||
        typedResponse.content ||
        typedResponse.response ||
        "No response received",
      provider: typedResponse.provider || "unknown",
      model: typedResponse.model || "unknown",
      status: typedResponse.status || "success",
      error: typedResponse.error,
    };
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
    return this.request("/simple/rag", {
      method: "POST",
      body: JSON.stringify(request),
    });
  }

  // Project management methods
  async getProcessedProjects(): Promise<ProcessedProjectEntry[]> {
    return this.request("/api/processed_projects");
  }

  // Wiki projects endpoint - matches OpenAPI spec
  async getWikiProjects(): Promise<ProcessedProjectEntry[]> {
    return this.request("/wiki/projects");
  }

  async saveProcessedProject(request: {
    owner: string;
    repo: string;
    repo_type?: string;
    language?: string;
    wiki_structure?: any;
    generated_pages?: Record<string, any>;
    provider?: string;
    model?: string;
  }): Promise<{ id: string; message: string }> {
    return this.request("/api/processed_projects", {
      method: "POST",
      body: JSON.stringify(request),
    });
  }

  async deleteProjectCache(
    owner: string,
    repo: string,
    repo_type: string,
    language: string,
  ): Promise<{ message: string }> {
    const params = new URLSearchParams({
      owner,
      repo,
      repo_type,
      language,
    });

    return this.request(`/api/wiki_cache?${params}`, {
      method: "DELETE",
    });
  }

  // Root and health endpoints
  async root(): Promise<any> {
    return this.request("/");
  }

  async healthCheck(): Promise<any> {
    return this.request("/health");
  }
}

export const apiClient = new APIClient();
export default APIClient;
