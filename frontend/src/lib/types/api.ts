/**
 * TypeScript definitions for Grantha API
 * Generated from Python Pydantic models
 */

export interface WikiPage {
	id: string;
	title: string;
	content: string;
	filePaths: string[];
	importance: 'high' | 'medium' | 'low';
	relatedPages: string[];
}

export interface ProcessedProjectEntry {
	id: string;
	owner: string;
	repo: string;
	name: string;
	repo_type: string;
	submittedAt: number;
	language: string;
}

export interface RepoInfo {
	owner: string;
	repo: string;
	type: string;
	token?: string;
	localPath?: string;
	repoUrl?: string;
}

export interface WikiSection {
	id: string;
	title: string;
	pages: string[];
	subsections?: string[];
}

export interface WikiStructureModel {
	id: string;
	title: string;
	description: string;
	pages: WikiPage[];
	sections?: WikiSection[];
	rootSections?: string[];
	repo_url?: string;
	generated_at?: number;
}

export interface WikiCacheData {
	wiki_structure: WikiStructureModel;
	generated_pages: Record<string, WikiPage>;
	repo_url?: string;
	repo?: RepoInfo;
	provider?: string;
	model?: string;
}

export interface Model {
	id: string;
	name: string;
}

export interface Provider {
	id: string;
	name: string;
	models: Model[];
	supportsCustomModel?: boolean;
}

export interface ModelConfig {
	providers: Provider[];
	defaultProvider: string;
}

export interface AuthorizationConfig {
	code: string;
}

export interface AuthStatus {
	auth_required: boolean;
}

export interface AuthValidationResponse {
	success: boolean;
}

export interface ChatMessage {
	role: 'user' | 'assistant' | 'system';
	content: string;
	timestamp?: number;
	id?: string;
}

export interface ChatConversation {
	id: string;
	title: string;
	messages: ChatMessage[];
	createdAt: number;
	updatedAt: number;
	model?: string;
	provider?: string;
}

export interface ChatRequest {
	messages: ChatMessage[];
	model?: string;
	provider?: string;
	stream?: boolean;
	temperature?: number;
	max_tokens?: number;
}

export interface ChatResponse {
	content: string;
	model: string;
	provider: string;
	usage?: Record<string, any>;
	finish_reason?: string;
}

export interface WikiGenerationRequest {
	repo_url: string;
	language?: string;
	provider?: string;
	model?: string;
	token?: string;
	repo_type?: string;
}

export interface WikiCacheRequest {
	repo: RepoInfo;
	language: string;
	wiki_structure: WikiStructureModel;
	generated_pages: Record<string, WikiPage>;
	provider: string;
	model: string;
}

export interface WikiExportRequest {
	repo_url: string;
	pages: WikiPage[];
	format: 'markdown' | 'json';
}

export interface DeepResearchRequest {
	query: string;
	repo_url: string;
	language?: string;
	provider?: string;
	model?: string;
	token?: string;
	repo_type?: string;
}

export interface SimpleRequest {
	user_query: string;
	repo_url?: string;
	provider?: string;
	model?: string;
	language?: string;
	token?: string;
	repo_type?: string;
}

export interface RAGRequest {
	query: string;
	repo_url: string;
	provider?: string;
	model?: string;
	language?: string;
	token?: string;
	repo_type?: string;
	k?: number;
}

export interface ApiError {
	message: string;
	code?: string;
	details?: any;
}

export interface LoadingState {
	isLoading: boolean;
	message?: string;
}

// WebSocket message types
export interface WebSocketMessage {
	type: string;
	data: any;
	timestamp: number;
}

export interface ChatStreamMessage extends WebSocketMessage {
	type: 'chat_stream';
	data: {
		session_id: string;
		content?: string;
		done: boolean;
		model?: string;
		provider?: string;
	};
}

// UI State types
export interface UIState {
	sidebarOpen: boolean;
	theme: 'light' | 'dark' | 'system';
	currentPage: string;
}

export interface AgentInfo {
	id: string;
	name: string;
	description: string;
	capabilities: string[];
	status: 'active' | 'inactive' | 'busy';
}

export interface AgentTask {
	id: string;
	agentId: string;
	title: string;
	description: string;
	status: 'pending' | 'running' | 'completed' | 'failed';
	createdAt: number;
	completedAt?: number;
	result?: any;
	error?: string;
}

// Additional types for API client
export interface AuthRequest {
	username: string;
	password: string;
}

export interface AuthResponse {
	access_token: string;
	token_type: string;
	user: {
		id: string;
		username: string;
		email?: string;
	};
}

// Map to existing types for compatibility
export interface AuthStatus {
	auth_required: boolean;
}

export interface AuthValidationResponse {
	success: boolean;
}

export interface ChatSession {
	id: string;
	title: string;
	created_at: number;
	updated_at: number;
	message_count: number;
}

export interface WikiEntry {
	id: string;
	title: string;
	content: string;
	created_at: number;
	updated_at: number;
	tags: string[];
}

export interface ResearchQuery {
	query: string;
	type: 'basic' | 'comprehensive' | 'deep';
	include_sources?: boolean;
	provider?: string;
	model?: string;
}

export interface ResearchResult {
	id: string;
	query: string;
	result: string;
	sources?: string[];
	created_at: number;
	provider: string;
	model: string;
}

export interface APIError {
	error: string;
	message: string;
	code: number;
}