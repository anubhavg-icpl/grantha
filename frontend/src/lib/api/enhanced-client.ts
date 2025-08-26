/**
 * Enhanced API Client with Deepwiki Integration
 * Combines Grantha's robust API client with Deepwiki features
 */

import { apiClient } from './client.js';
import type { 
  ChatCompletionRequest, 
  ChatStreamData,
  UnifiedAPIError,
  WikiGenerationExtended,
  UnifiedResearchQuery,
  UnifiedModelConfig
} from '../types/shared.js';
import { deepwikiClient } from '../utils/deepwiki-integration.js';

export class EnhancedAPIClient {
  private wsConnections: Map<string, WebSocket> = new Map();
  
  /**
   * Stream chat completion using WebSocket
   */
  async streamChat(
    request: ChatCompletionRequest,
    onMessage: (data: ChatStreamData) => void,
    onError?: (error: UnifiedAPIError) => void,
    onComplete?: () => void
  ): Promise<() => void> {
    // Generate unique connection ID
    const connectionId = `chat-${Date.now()}`;
    
    // Create WebSocket connection
    const ws = deepwikiClient.connect(
      request,
      onMessage,
      (error) => {
        if (onError) {
          const apiError: UnifiedAPIError = {
            message: 'WebSocket connection error',
            code: 'WS_ERROR',
            details: error,
            type: 'network_error'
          };
          onError(apiError);
        }
      },
      () => {
        this.wsConnections.delete(connectionId);
        if (onComplete) onComplete();
      }
    );
    
    this.wsConnections.set(connectionId, ws);
    
    // Return cleanup function
    return () => {
      const connection = this.wsConnections.get(connectionId);
      if (connection) {
        connection.close();
        this.wsConnections.delete(connectionId);
      }
    };
  }
  
  /**
   * Generate comprehensive wiki documentation
   */
  async generateWiki(params: WikiGenerationExtended) {
    const response = await apiClient.request('/wiki/generate', {
      method: 'POST',
      body: JSON.stringify({
        repo_url: params.repo_url,
        language: params.language,
        provider: params.provider,
        model: params.model,
        token: params.token,
        repo_type: params.repo_type,
        // Extended features
        include_diagrams: params.include_diagrams,
        include_architecture: params.include_architecture,
        depth_level: params.depth_level || 'comprehensive'
      })
    });
    
    return response;
  }
  
  /**
   * Perform deep research with RAG integration
   */
  async deepResearch(query: UnifiedResearchQuery) {
    if (query.type === 'deep' && query.k) {
      // Use RAG for deep research
      return apiClient.request('/rag/query', {
        method: 'POST',
        body: JSON.stringify({
          query: query.query,
          repo_url: query.repo_url,
          provider: query.provider,
          model: query.model,
          language: query.language,
          token: query.token,
          k: query.k
        })
      });
    } else {
      // Use standard research endpoint
      return apiClient.request('/research/deep', {
        method: 'POST',
        body: JSON.stringify({
          query: query.query,
          repo_url: query.repo_url,
          provider: query.provider,
          model: query.model,
          language: query.language,
          token: query.token
        })
      });
    }
  }
  
  /**
   * Get unified model configuration
   */
  async getUnifiedModelConfig(): Promise<UnifiedModelConfig> {
    const config = await apiClient.getModelConfig();
    
    // Enhance with additional capabilities
    return {
      ...config,
      providers: config.providers.map(provider => ({
        ...provider,
        supportsStreaming: true, // All providers support streaming via WebSocket
        models: provider.models.map(model => ({
          ...model,
          capabilities: this.getModelCapabilities(provider.id, model.id)
        }))
      })),
      defaultModel: this.getDefaultModel(config)
    };
  }
  
  /**
   * Get model capabilities based on provider and model
   */
  private getModelCapabilities(providerId: string, modelId: string): string[] {
    const capabilities: string[] = ['chat', 'completion'];
    
    // Add provider-specific capabilities
    if (providerId === 'google') {
      capabilities.push('vision', 'embedding', 'long-context');
    } else if (providerId === 'openai') {
      capabilities.push('function-calling', 'vision', 'embedding');
    } else if (providerId === 'anthropic') {
      capabilities.push('long-context', 'vision');
    } else if (providerId === 'deepseek') {
      capabilities.push('code-generation', 'reasoning');
    } else if (providerId === 'groq') {
      capabilities.push('fast-inference');
    }
    
    // Add model-specific capabilities
    if (modelId.includes('gpt-4') || modelId.includes('claude-3') || modelId.includes('gemini-pro')) {
      capabilities.push('advanced-reasoning');
    }
    
    return capabilities;
  }
  
  /**
   * Get default model from configuration
   */
  private getDefaultModel(config: any): string {
    const defaultProvider = config.providers.find(
      (p: any) => p.id === config.defaultProvider
    );
    return defaultProvider?.models[0]?.id || 'gpt-3.5-turbo';
  }
  
  /**
   * Export wiki in various formats
   */
  async exportWiki(repoUrl: string, format: 'markdown' | 'json' | 'pdf' = 'markdown') {
    const response = await apiClient.request(`/export/wiki?repo_url=${encodeURIComponent(repoUrl)}&format=${format}`, {
      method: 'GET'
    });
    
    if (format === 'markdown' || format === 'pdf') {
      // Return as blob for file download
      return new Blob([response as any], { 
        type: format === 'pdf' ? 'application/pdf' : 'text/markdown' 
      });
    }
    
    return response;
  }
  
  /**
   * Get repository structure for local repos
   */
  async getLocalRepoStructure(path: string) {
    return apiClient.request('/local_repo/structure', {
      method: 'POST',
      body: JSON.stringify({ path })
    });
  }
  
  /**
   * Validate authentication
   */
  async validateAuth(code: string): Promise<boolean> {
    try {
      const response = await apiClient.request('/auth/validate', {
        method: 'POST',
        body: JSON.stringify({ code })
      });
      return response.success === true;
    } catch {
      return false;
    }
  }
  
  /**
   * Get language configuration
   */
  async getLanguageConfig() {
    return apiClient.request('/lang/config');
  }
  
  /**
   * Clean up all WebSocket connections
   */
  cleanup() {
    this.wsConnections.forEach(ws => ws.close());
    this.wsConnections.clear();
  }
}

// Export singleton instance
export const enhancedAPI = new EnhancedAPIClient();