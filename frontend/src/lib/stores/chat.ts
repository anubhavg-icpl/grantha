/**
 * Chat Store
 * Manages chat conversations, messages, and real-time streaming
 */

import { writable, derived, get } from "svelte/store";
import { browser } from "$app/environment";
import { apiClient } from "$api/client";
import { wsClient } from "$lib/websocket/client";
import { modelsActions } from "./models";
import type { ChatMessage, ChatRequest, ChatResponse } from "$types/api";

export interface ChatConversation {
  id: string;
  title: string;
  messages: ChatMessage[];
  createdAt: number;
  updatedAt: number;
  model?: string;
  provider?: string;
}

interface ChatState {
  conversations: ChatConversation[];
  activeConversationId: string | null;
  isStreaming: boolean;
  streamingMessage: string;
  isLoading: boolean;
  error: string | null;
  streamSessionId: string | null;
}

// Initialize chat state
const initialState: ChatState = {
  conversations: [],
  activeConversationId: null,
  isStreaming: false,
  streamingMessage: "",
  isLoading: false,
  error: null,
  streamSessionId: null,
};

// Create writable store
export const chatState = writable<ChatState>(initialState);

// Derived stores
export const activeConversation = derived(chatState, ($chatState) => {
  if (!$chatState.activeConversationId) return null;
  return (
    $chatState.conversations.find(
      (c) => c.id === $chatState.activeConversationId,
    ) || null
  );
});

export const hasConversations = derived(
  chatState,
  ($chatState) => $chatState.conversations.length > 0,
);

export const canSendMessage = derived(
  chatState,
  ($chatState) => !$chatState.isLoading && !$chatState.isStreaming,
);

/**
 * Chat actions
 */
export const chatActions = {
  // Create new conversation
  createConversation(title?: string): string {
    const id = `conv_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
    const conversation: ChatConversation = {
      id,
      title: title || "New Chat",
      messages: [],
      createdAt: Date.now(),
      updatedAt: Date.now(),
    };

    chatState.update((state) => ({
      ...state,
      conversations: [conversation, ...state.conversations],
      activeConversationId: id,
      error: null,
    }));

    chatActions.saveToStorage();
    return id;
  },

  // Select conversation
  selectConversation(conversationId: string): void {
    chatState.update((state) => ({
      ...state,
      activeConversationId: conversationId,
      error: null,
    }));
    chatActions.saveToStorage();
  },

  // Delete conversation
  deleteConversation(conversationId: string): void {
    chatState.update((state) => {
      const conversations = state.conversations.filter(
        (c) => c.id !== conversationId,
      );
      const activeId =
        state.activeConversationId === conversationId
          ? conversations[0]?.id || null
          : state.activeConversationId;

      return {
        ...state,
        conversations,
        activeConversationId: activeId,
      };
    });
    chatActions.saveToStorage();
  },

  // Update conversation title
  updateConversationTitle(conversationId: string, title: string): void {
    chatState.update((state) => ({
      ...state,
      conversations: state.conversations.map((c) =>
        c.id === conversationId ? { ...c, title, updatedAt: Date.now() } : c,
      ),
    }));
    chatActions.saveToStorage();
  },

  // Add message to conversation
  addMessage(conversationId: string, message: ChatMessage): void {
    chatState.update((state) => ({
      ...state,
      conversations: state.conversations.map((c) =>
        c.id === conversationId
          ? {
              ...c,
              messages: [
                ...c.messages,
                { ...message, timestamp: message.timestamp || Date.now() },
              ],
              updatedAt: Date.now(),
            }
          : c,
      ),
    }));
    chatActions.saveToStorage();
  },

  // Send message with streaming
  async sendMessage(message: string, useStreaming = true): Promise<void> {
    const state = get(chatState);
    const activeId = state.activeConversationId;

    if (!activeId) {
      chatActions.createConversation();
      const newState = get(chatState);
      return chatActions.sendMessage(message, useStreaming);
    }

    // Add user message
    const userMessage: ChatMessage = {
      role: "user",
      content: message,
      timestamp: Date.now(),
    };
    chatActions.addMessage(activeId, userMessage);

    // Get current model selection
    const { provider, model } = modelsActions.getCurrentSelection();

    // Prepare chat request
    const conversation = get(activeConversation);
    const chatRequest: ChatRequest = {
      messages: conversation?.messages || [userMessage],
      provider: provider || undefined,
      model: model || undefined,
      stream: useStreaming,
    };

    if (useStreaming) {
      await chatActions.sendStreamingMessageWithFallback(activeId, chatRequest);
    } else {
      await chatActions.sendRegularMessage(activeId, chatRequest);
    }
  },

  // Send regular (non-streaming) message
  async sendRegularMessage(
    conversationId: string,
    chatRequest: ChatRequest,
  ): Promise<void> {
    chatState.update((state) => ({ ...state, isLoading: true, error: null }));

    try {
      const response: ChatResponse =
        await apiClient.chatCompletion(chatRequest);

      const assistantMessage: ChatMessage = {
        role: "assistant",
        content: response.content,
        timestamp: Date.now(),
      };

      chatActions.addMessage(conversationId, assistantMessage);

      // Update conversation with model info
      chatState.update((state) => ({
        ...state,
        conversations: state.conversations.map((c) =>
          c.id === conversationId
            ? { ...c, model: response.model, provider: response.provider }
            : c,
        ),
        isLoading: false,
      }));
    } catch (error) {
      console.error("Chat completion failed:", error);
      chatState.update((state) => ({
        ...state,
        isLoading: false,
        error:
          error instanceof Error ? error.message : "Failed to send message",
      }));
    }
  },

  // Send streaming message using Server-Sent Events
  async sendStreamingMessage(
    conversationId: string,
    chatRequest: ChatRequest,
  ): Promise<void> {
    chatState.update((state) => ({
      ...state,
      isStreaming: true,
      streamingMessage: "",
      error: null,
    }));

    try {
      // Get the streaming response
      const stream = await apiClient.chatCompletionStream({
        messages: chatRequest.messages,
        model: chatRequest.model,
        provider: chatRequest.provider,
        temperature: chatRequest.temperature,
        max_tokens: chatRequest.max_tokens,
      });

      const reader = stream.getReader();
      const decoder = new TextDecoder();

      try {
        while (true) {
          const { done, value } = await reader.read();
          if (done) break;

          const chunk = decoder.decode(value, { stream: true });
          const lines = chunk.split("\n");

          for (const line of lines) {
            if (line.startsWith("data: ")) {
              const data = line.slice(6); // Remove 'data: ' prefix
              if (data.trim() === "") continue;

              try {
                const parsed = JSON.parse(data);

                if (parsed.error) {
                  // Handle error in stream
                  chatState.update((state) => ({
                    ...state,
                    isStreaming: false,
                    streamingMessage: "",
                    error: parsed.error,
                  }));
                  return;
                }

                if (parsed.done) {
                  // Stream completed
                  const currentState = get(chatState);
                  const finalMessage: ChatMessage = {
                    role: "assistant",
                    content: currentState.streamingMessage,
                    timestamp: Date.now(),
                  };

                  chatActions.addMessage(conversationId, finalMessage);

                  // Update conversation with model info
                  chatState.update((state) => ({
                    ...state,
                    conversations: state.conversations.map((c) =>
                      c.id === conversationId
                        ? {
                            ...c,
                            model: parsed.model,
                            provider: parsed.provider,
                          }
                        : c,
                    ),
                    isStreaming: false,
                    streamingMessage: "",
                    streamSessionId: null,
                  }));
                  return;
                } else if (parsed.content) {
                  // Append to streaming message
                  chatState.update((state) => ({
                    ...state,
                    streamingMessage: state.streamingMessage + parsed.content,
                  }));
                }
              } catch (parseError) {
                console.error(
                  "Failed to parse streaming data:",
                  parseError,
                  data,
                );
              }
            }
          }
        }
      } finally {
        reader.releaseLock();
      }
    } catch (error) {
      console.error("Streaming failed:", error);
      chatState.update((state) => ({
        ...state,
        isStreaming: false,
        streamingMessage: "",
        streamSessionId: null,
        error: error instanceof Error ? error.message : "Streaming failed",
      }));
    }
  },

  // Send streaming message with fallback to WebSocket
  async sendStreamingMessageWithFallback(
    conversationId: string,
    chatRequest: ChatRequest,
  ): Promise<void> {
    try {
      // Try Server-Sent Events first
      await chatActions.sendStreamingMessage(conversationId, chatRequest);
    } catch (sseError) {
      console.warn(
        "SSE streaming failed, falling back to WebSocket:",
        sseError,
      );

      // Fallback to WebSocket streaming
      chatState.update((state) => ({
        ...state,
        isStreaming: true,
        streamingMessage: "",
        error: null,
      }));

      try {
        // Connect WebSocket if not connected
        if (wsClient.getStatus() !== "connected") {
          wsClient.connect();
        }

        // Generate a session ID for this stream
        const sessionId = `stream_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
        chatState.update((state) => ({ ...state, streamSessionId: sessionId }));

        // Send the chat request through WebSocket
        wsClient.send({
          type: "chat_stream_start",
          data: {
            session_id: sessionId,
            ...chatRequest,
          },
        });

        // Subscribe to stream messages
        const unsubscribe = wsClient.onChatStream((message) => {
          if (message.data.session_id === sessionId) {
            if (message.data.done) {
              // Stream completed
              const finalMessage: ChatMessage = {
                role: "assistant",
                content: get(chatState).streamingMessage,
                timestamp: Date.now(),
              };

              chatActions.addMessage(conversationId, finalMessage);

              chatState.update((state) => ({
                ...state,
                isStreaming: false,
                streamingMessage: "",
                streamSessionId: null,
              }));

              unsubscribe();
            } else {
              // Append to streaming message
              chatState.update((state) => ({
                ...state,
                streamingMessage:
                  state.streamingMessage + (message.data.content || ""),
              }));
            }
          }
        });
      } catch (wsError) {
        console.error("WebSocket streaming also failed:", wsError);
        chatState.update((state) => ({
          ...state,
          isStreaming: false,
          streamingMessage: "",
          streamSessionId: null,
          error: "Both streaming methods failed. Please try again.",
        }));
      }
    }
  },

  // Stop streaming
  stopStreaming(): void {
    const state = get(chatState);
    if (state.streamSessionId) {
      wsClient.send({
        type: "chat_stream_stop",
        data: {
          session_id: state.streamSessionId,
        },
      });
    }

    chatState.update((state) => ({
      ...state,
      isStreaming: false,
      streamingMessage: "",
      streamSessionId: null,
    }));
  },

  // Clear all conversations
  clearAllConversations(): void {
    chatState.update((state) => ({
      ...state,
      conversations: [],
      activeConversationId: null,
    }));
    chatActions.saveToStorage();
  },

  // Save to localStorage
  saveToStorage(): void {
    if (!browser) return;

    const state = get(chatState);
    const toSave = {
      conversations: state.conversations,
      activeConversationId: state.activeConversationId,
    };

    localStorage.setItem("grantha-chat-state", JSON.stringify(toSave));
  },

  // Load from localStorage
  loadFromStorage(): void {
    if (!browser) return;

    try {
      const saved = localStorage.getItem("grantha-chat-state");
      if (saved) {
        const { conversations, activeConversationId } = JSON.parse(saved);
        chatState.update((state) => ({
          ...state,
          conversations: conversations || [],
          activeConversationId: activeConversationId || null,
        }));
      }
    } catch (error) {
      console.error("Failed to load chat state from storage:", error);
    }
  },

  // Clear error
  clearError(): void {
    chatState.update((state) => ({ ...state, error: null }));
  },
};

// Load saved state on initialization
if (browser) {
  chatActions.loadFromStorage();
}
