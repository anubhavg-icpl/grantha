/**
 * Shared type definitions for Grantha-Deepwiki integration
 * These types bridge the gap between the two projects
 */

// Base Wiki types that both projects share
export interface WikiPageBase {
  id: string;
  title: string;
  content: string;
  filePaths: string[];
  importance: "high" | "medium" | "low";
  relatedPages: string[];
}

// Extended Wiki types from deepwiki
export interface WikiPageExtended extends WikiPageBase {
  parentId?: string;
  isSection?: boolean;
  children?: string[];
}

// Wiki section for tree structure
export interface WikiSection {
  id: string;
  title: string;
  pages?: string[];
  subsections?: string[];
}

// Unified Repository Information
export interface RepoInfoUnified {
  owner: string;
  repo: string;
  type: string;
  token?: string | null;
  localPath?: string | null;
  repoUrl?: string | null;
}

// Unified Chat Message interface
export interface UnifiedChatMessage {
  role: "user" | "assistant" | "system";
  content: string;
  timestamp?: number;
  id?: string;
  metadata?: Record<string, any>;
}

// Unified WebSocket message interface
export interface UnifiedWebSocketMessage<T = any> {
  type: string;
  data: T;
  timestamp: number;
  sessionId?: string;
}

// Chat Stream Data for real-time messaging
export interface ChatStreamData {
  session_id: string;
  content?: string;
  done: boolean;
  model?: string;
  provider?: string;
  usage?: Record<string, any>;
  error?: string;
}

// Deepwiki-specific Chat Completion Request
export interface ChatCompletionRequest {
  repo_url: string;
  messages: UnifiedChatMessage[];
  filePath?: string;
  token?: string;
  type?: string;
  provider?: string;
  model?: string;
  language?: string;
  excluded_dirs?: string;
  excluded_files?: string;
  stream?: boolean;
  temperature?: number;
  max_tokens?: number;
}

// Wiki Generation with extended features
export interface WikiGenerationExtended {
  repo_url: string;
  language?: string;
  provider?: string;
  model?: string;
  token?: string;
  repo_type?: string;
  // Deepwiki-specific fields
  include_diagrams?: boolean;
  include_architecture?: boolean;
  depth_level?: "basic" | "comprehensive" | "deep";
}

// Research Query with unified approach
export interface UnifiedResearchQuery {
  query: string;
  repo_url?: string;
  type?: "basic" | "comprehensive" | "deep";
  include_sources?: boolean;
  provider?: string;
  model?: string;
  language?: string;
  token?: string;
  k?: number; // For RAG
}

// Unified API Error
export interface UnifiedAPIError {
  message: string;
  code?: string | number;
  details?: any;
  type?: "client_error" | "server_error" | "network_error";
}

// Model Configuration shared between projects
export interface UnifiedModelConfig {
  providers: Array<{
    id: string;
    name: string;
    models: Array<{
      id: string;
      name: string;
      capabilities?: string[];
    }>;
    supportsCustomModel?: boolean;
    supportsStreaming?: boolean;
  }>;
  defaultProvider: string;
  defaultModel?: string;
}

// Export utilities for type checking
export const isWikiPageExtended = (
  page: WikiPageBase,
): page is WikiPageExtended => {
  return "parentId" in page || "isSection" in page || "children" in page;
};

export const isChatStreamData = (data: any): data is ChatStreamData => {
  return (
    data && typeof data === "object" && "session_id" in data && "done" in data
  );
};

// Type guards for runtime validation
export const isUnifiedAPIError = (error: any): error is UnifiedAPIError => {
  return error && typeof error === "object" && "message" in error;
};

// Re-export existing types for convenience
export type { WikiPage, RepoInfo, ChatMessage } from "./api.js";
