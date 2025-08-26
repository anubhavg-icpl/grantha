<script lang="ts">
  import { onMount, onDestroy } from 'svelte';
  import { Send, Loader2, Bot, User, Copy, Check, Trash2, Download, Settings, Sparkles, X, MessageSquare, Plus, Moon, Sun } from 'lucide-svelte';
  import { wsClient } from '$lib/websocket/client.js';
  import { apiClient } from '$lib/api/client.js';
  import type { ChatMessage } from '$lib/types/api.js';
  import ThemeToggle from '$lib/components/ThemeToggle.svelte';

  interface Conversation {
    id: string;
    title: string;
    messages: ChatMessage[];
    createdAt: number;
    updatedAt: number;
    model: string;
    provider: string;
  }

  interface ModelProvider {
    id: string;
    name: string;
    models: Array<{ id: string; name: string; }>;
  }

  // State variables
  let messages: ChatMessage[] = $state([]);
  let inputMessage = $state('');
  let isStreaming = $state(false);
  let streamingContent = $state('');
  let selectedProvider = $state('openai');
  let selectedModel = $state('gpt-3.5-turbo');
  let temperature = $state(0.7);
  let maxTokens = $state(2000);
  let conversations: Conversation[] = $state([]);
  let currentConversationId = $state<string | null>(null);
  let showSettings = $state(false);
  let copiedMessageId = $state<string | null>(null);
  let modelProviders: ModelProvider[] = $state([]);
  let isLoadingModels = $state(true);
  let sessionId = $state(`session_${Date.now()}`);
  
  let chatContainer: HTMLDivElement;
  let textareaElement: HTMLTextAreaElement;

  // Load model configuration
  async function loadModelConfig() {
    try {
      isLoadingModels = true;
      const config = await apiClient.getModelConfig();
      modelProviders = config.providers || [];
      if (config.defaultProvider) {
        selectedProvider = config.defaultProvider;
      }
      // Set first model as default if available
      const provider = modelProviders.find(p => p.id === selectedProvider);
      if (provider && provider.models.length > 0) {
        selectedModel = provider.models[0].id;
      }
    } catch (error) {
      console.error('Failed to load model config:', error);
      // Fallback providers
      modelProviders = [
        {
          id: 'openai',
          name: 'OpenAI',
          models: [
            { id: 'gpt-3.5-turbo', name: 'GPT-3.5 Turbo' },
            { id: 'gpt-4', name: 'GPT-4' }
          ]
        }
      ];
    } finally {
      isLoadingModels = false;
    }
  }

  // Load conversations from localStorage
  function loadConversations() {
    const saved = localStorage.getItem('grantha_conversations');
    if (saved) {
      try {
        conversations = JSON.parse(saved);
      } catch (e) {
        conversations = [];
      }
    }
  }

  // Save conversations to localStorage
  function saveConversations() {
    localStorage.setItem('grantha_conversations', JSON.stringify(conversations));
  }

  // Create new conversation
  function createNewConversation() {
    const newConversation: Conversation = {
      id: `conv_${Date.now()}`,
      title: 'New Conversation',
      messages: [],
      createdAt: Date.now(),
      updatedAt: Date.now(),
      model: selectedModel,
      provider: selectedProvider
    };
    conversations = [newConversation, ...conversations];
    currentConversationId = newConversation.id;
    messages = [];
    sessionId = `session_${Date.now()}`;
    saveConversations();
  }

  // Load conversation
  function loadConversation(conversationId: string) {
    const conversation = conversations.find(c => c.id === conversationId);
    if (conversation) {
      currentConversationId = conversationId;
      messages = [...conversation.messages];
      selectedModel = conversation.model || selectedModel;
      selectedProvider = conversation.provider || selectedProvider;
      sessionId = `session_${Date.now()}`;
    }
  }

  // Update conversation title based on first message
  function updateConversationTitle() {
    if (!currentConversationId || messages.length === 0) return;
    
    const conversation = conversations.find(c => c.id === currentConversationId);
    if (conversation && conversation.title === 'New Conversation') {
      const firstUserMessage = messages.find(m => m.role === 'user');
      if (firstUserMessage) {
        conversation.title = firstUserMessage.content.slice(0, 50) + (firstUserMessage.content.length > 50 ? '...' : '');
        conversation.updatedAt = Date.now();
        conversations = conversations;
        saveConversations();
      }
    }
  }

  // Delete conversation
  function deleteConversation(conversationId: string, event?: Event) {
    event?.stopPropagation();
    if (!confirm('Delete this conversation?')) return;
    
    conversations = conversations.filter(c => c.id !== conversationId);
    if (currentConversationId === conversationId) {
      currentConversationId = null;
      messages = [];
    }
    saveConversations();
  }

  // Connect to WebSocket
  function connectWebSocket() {
    wsClient.connect();
    
    // Listen for streaming messages
    const unsubscribe = wsClient.onChatStream((message) => {
      if (message.data.session_id === sessionId) {
        if (message.data.content) {
          streamingContent += message.data.content;
          if (messages.length > 0 && messages[messages.length - 1].role === 'assistant') {
            messages[messages.length - 1].content = streamingContent;
            messages = messages;
            scrollToBottom();
          }
        }
        
        if (message.data.done) {
          isStreaming = false;
          streamingContent = '';
          saveCurrentConversation();
          updateConversationTitle();
        }
      }
    });
    
    return unsubscribe;
  }

  // Send message via WebSocket
  async function sendMessage() {
    if (!inputMessage.trim() || isStreaming) return;

    // Create conversation if needed
    if (!currentConversationId) {
      createNewConversation();
    }

    const userMessage: ChatMessage = {
      role: 'user',
      content: inputMessage,
      timestamp: Date.now(),
      id: `msg_${Date.now()}`
    };

    messages = [...messages, userMessage];
    const messageToSend = inputMessage;
    inputMessage = '';
    isStreaming = true;
    streamingContent = '';

    // Auto-resize textarea
    if (textareaElement) {
      textareaElement.style.height = 'auto';
    }

    // Create assistant message placeholder
    const assistantMessage: ChatMessage = {
      role: 'assistant',
      content: '',
      timestamp: Date.now(),
      id: `msg_${Date.now() + 1}`
    };
    messages = [...messages, assistantMessage];
    scrollToBottom();

    // Send via WebSocket
    wsClient.sendChatMessage(sessionId, messageToSend);
    
    // Also try HTTP fallback if WebSocket fails
    setTimeout(async () => {
      if (isStreaming && !streamingContent) {
        try {
          const response = await apiClient.sendChatMessage(
            messages.slice(0, -1),
            selectedModel,
            selectedProvider
          );
          
          messages[messages.length - 1].content = response.content;
          messages = messages;
          isStreaming = false;
          saveCurrentConversation();
          updateConversationTitle();
        } catch (error) {
          console.error('HTTP fallback failed:', error);
          messages[messages.length - 1].content = 'Failed to get response. Please try again.';
          isStreaming = false;
        }
      }
    }, 5000); // 5 second timeout for WebSocket
  }

  // Save current conversation
  function saveCurrentConversation() {
    if (!currentConversationId) return;
    
    const conversation = conversations.find(c => c.id === currentConversationId);
    if (conversation) {
      conversation.messages = [...messages];
      conversation.model = selectedModel;
      conversation.provider = selectedProvider;
      conversation.updatedAt = Date.now();
      saveConversations();
    }
  }

  // Copy message to clipboard
  async function copyMessage(message: ChatMessage, event?: Event) {
    event?.stopPropagation();
    try {
      await navigator.clipboard.writeText(message.content);
      copiedMessageId = message.id;
      setTimeout(() => {
        copiedMessageId = null;
      }, 2000);
    } catch (error) {
      console.error('Failed to copy:', error);
    }
  }

  // Delete message
  function deleteMessage(messageId: string | undefined, event?: Event) {
    event?.stopPropagation();
    if (!messageId) return;
    messages = messages.filter(m => m.id !== messageId);
    saveCurrentConversation();
  }

  // Export conversation
  function exportConversation() {
    if (messages.length === 0) return;

    const content = messages
      .map(m => `${m.role.toUpperCase()}: ${m.content}`)
      .join('\n\n---\n\n');
    
    const blob = new Blob([content], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `conversation_${currentConversationId || 'export'}_${Date.now()}.txt`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  }

  // Clear all messages
  function clearMessages() {
    if (!confirm('Clear all messages in this conversation?')) return;
    
    messages = [];
    if (currentConversationId) {
      const conversation = conversations.find(c => c.id === currentConversationId);
      if (conversation) {
        conversation.messages = [];
        saveConversations();
      }
    }
  }

  // Scroll to bottom
  function scrollToBottom() {
    if (chatContainer) {
      requestAnimationFrame(() => {
        chatContainer.scrollTop = chatContainer.scrollHeight;
      });
    }
  }

  // Handle Enter key
  function handleKeydown(event: KeyboardEvent) {
    if (event.key === 'Enter' && !event.shiftKey) {
      event.preventDefault();
      sendMessage();
    }
  }

  // Auto-resize textarea
  function autoResizeTextarea() {
    if (textareaElement) {
      textareaElement.style.height = 'auto';
      textareaElement.style.height = Math.min(textareaElement.scrollHeight, 200) + 'px';
    }
  }

  // Stop streaming
  function stopStreaming() {
    isStreaming = false;
    streamingContent = '';
  }

  let unsubscribeWebSocket: (() => void) | null = null;

  onMount(() => {
    loadModelConfig();
    loadConversations();
    unsubscribeWebSocket = connectWebSocket();
    scrollToBottom();
  });

  onDestroy(() => {
    if (unsubscribeWebSocket) {
      unsubscribeWebSocket();
    }
    wsClient.disconnect();
  });

  // Computed values
  let currentConversation = $derived(conversations.find(c => c.id === currentConversationId));
  let currentProvider = $derived(modelProviders.find(p => p.id === selectedProvider));
  let availableModels = $derived(currentProvider?.models || []);
</script>

<svelte:head>
  <title>Chat - Grantha</title>
</svelte:head>

<div class="flex h-screen bg-background">
  <!-- Sidebar -->
  <div class="w-80 bg-card border-r border-border flex flex-col">
    <!-- New Chat Button -->
    <div class="p-4 border-b border-border">
      <button
        onclick={createNewConversation}
        class="w-full flex items-center justify-center gap-2 px-4 py-2.5 bg-primary text-primary-foreground rounded-lg hover:bg-primary/90 transition-all duration-200 font-medium"
      >
        <Plus class="w-5 h-5" />
        New Chat
      </button>
    </div>

    <!-- Conversations List -->
    <div class="flex-1 overflow-y-auto">
      <div class="p-2">
        <h3 class="px-3 py-2 text-xs font-semibold text-muted-foreground uppercase tracking-wider">Recent Conversations</h3>
        {#each conversations as conversation}
          <button
            onclick={() => loadConversation(conversation.id)}
            class="w-full group mb-1 relative"
          >
            <div class="flex items-center justify-between px-3 py-2.5 rounded-lg hover:bg-accent transition-colors {currentConversationId === conversation.id ? 'bg-accent' : ''}">
              <div class="flex-1 text-left min-w-0">
                <div class="text-sm font-medium truncate">{conversation.title}</div>
                <div class="text-xs text-muted-foreground">
                  {new Date(conversation.updatedAt || conversation.createdAt).toLocaleDateString()}
                </div>
              </div>
              <button
                onclick={(e) => deleteConversation(conversation.id, e)}
                class="opacity-0 group-hover:opacity-100 p-1.5 hover:bg-destructive/20 rounded transition-all"
              >
                <Trash2 class="w-4 h-4 text-destructive" />
              </button>
            </div>
          </button>
        {/each}
        {#if conversations.length === 0}
          <div class="px-3 py-8 text-center">
            <MessageSquare class="w-12 h-12 mx-auto mb-3 text-muted-foreground/50" />
            <p class="text-sm text-muted-foreground">No conversations yet</p>
            <p class="text-xs text-muted-foreground mt-1">Start a new chat to begin</p>
          </div>
        {/if}
      </div>
    </div>

    <!-- Sidebar Footer -->
    <div class="p-4 border-t border-border space-y-3">
      <div class="flex items-center justify-between">
        <span class="text-sm text-muted-foreground">Theme</span>
        <ThemeToggle />
      </div>
      <button
        onclick={() => showSettings = !showSettings}
        class="w-full flex items-center justify-center gap-2 px-3 py-2 text-sm border border-border rounded-lg hover:bg-accent transition-colors"
      >
        <Settings class="w-4 h-4" />
        Model Settings
      </button>
    </div>
  </div>

  <!-- Main Chat Area -->
  <div class="flex-1 flex flex-col">
    <!-- Header -->
    <div class="bg-card border-b border-border px-6 py-4">
      <div class="flex items-center justify-between">
        <div>
          <h1 class="text-xl font-semibold">
            {currentConversation ? currentConversation.title : 'New Chat'}
          </h1>
          <div class="flex items-center gap-2 mt-1">
            <span class="text-sm text-muted-foreground">
              {selectedProvider} / {selectedModel}
            </span>
            {#if isStreaming}
              <span class="flex items-center gap-1 text-xs text-green-500">
                <span class="w-2 h-2 bg-green-500 rounded-full animate-pulse"></span>
                Streaming
              </span>
            {/if}
          </div>
        </div>
        <div class="flex items-center gap-2">
          <button
            onclick={exportConversation}
            class="p-2 hover:bg-accent rounded-lg transition-colors"
            title="Export conversation"
            disabled={messages.length === 0}
          >
            <Download class="w-5 h-5" />
          </button>
          <button
            onclick={clearMessages}
            class="p-2 hover:bg-accent rounded-lg transition-colors"
            title="Clear messages"
            disabled={messages.length === 0}
          >
            <Trash2 class="w-5 h-5" />
          </button>
        </div>
      </div>
    </div>

    <!-- Messages -->
    <div 
      bind:this={chatContainer}
      class="flex-1 overflow-y-auto px-4 py-6 scrollbar-thin"
    >
      <div class="max-w-4xl mx-auto space-y-6">
        {#each messages as message (message.id)}
          <div class="flex gap-4 {message.role === 'user' ? 'flex-row-reverse' : ''}">
            <div class="flex-shrink-0">
              {#if message.role === 'user'}
                <div class="w-10 h-10 bg-primary rounded-lg flex items-center justify-center">
                  <User class="w-6 h-6 text-primary-foreground" />
                </div>
              {:else}
                <div class="w-10 h-10 bg-secondary rounded-lg flex items-center justify-center">
                  <Bot class="w-6 h-6 text-secondary-foreground" />
                </div>
              {/if}
            </div>
            
            <div class="flex-1 group max-w-[85%]">
              <div class="relative">
                <div class="{message.role === 'user' 
                  ? 'bg-primary text-primary-foreground rounded-2xl rounded-tr-sm' 
                  : 'bg-card border border-border rounded-2xl rounded-tl-sm'} px-4 py-3 shadow-sm">
                  <div class="prose prose-sm max-w-none dark:prose-invert">
                    {message.content || ''}
                    {#if message.role === 'assistant' && isStreaming && messages[messages.length - 1].id === message.id}
                      <span class="inline-block w-1 h-4 bg-primary animate-pulse ml-0.5"></span>
                    {/if}
                  </div>
                </div>
                
                <!-- Message Actions -->
                <div class="absolute -bottom-7 {message.role === 'user' ? 'right-0' : 'left-0'} flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                  <button
                    onclick={(e) => copyMessage(message, e)}
                    class="p-1.5 bg-card border border-border hover:bg-accent rounded-lg transition-colors"
                    title="Copy"
                  >
                    {#if copiedMessageId === message.id}
                      <Check class="w-3.5 h-3.5 text-green-500" />
                    {:else}
                      <Copy class="w-3.5 h-3.5" />
                    {/if}
                  </button>
                  <button
                    onclick={(e) => deleteMessage(message.id, e)}
                    class="p-1.5 bg-card border border-border hover:bg-accent rounded-lg transition-colors"
                    title="Delete"
                  >
                    <Trash2 class="w-3.5 h-3.5" />
                  </button>
                </div>
              </div>
            </div>
          </div>
        {/each}
        
        {#if messages.length === 0}
          <div class="text-center py-20">
            <div class="inline-flex items-center justify-center w-20 h-20 bg-primary/10 rounded-full mb-6">
              <Sparkles class="w-10 h-10 text-primary" />
            </div>
            <h2 class="text-2xl font-bold mb-3">Welcome to Grantha Chat</h2>
            <p class="text-muted-foreground max-w-md mx-auto">
              Ask me anything about coding, documentation, research, or any topic you'd like to explore.
            </p>
            <div class="flex flex-wrap gap-2 justify-center mt-6">
              <button
                onclick={() => { inputMessage = "Help me write a Python function"; }}
                class="px-4 py-2 bg-card border border-border rounded-lg hover:bg-accent transition-colors text-sm"
              >
                Write Python code
              </button>
              <button
                onclick={() => { inputMessage = "Explain quantum computing"; }}
                class="px-4 py-2 bg-card border border-border rounded-lg hover:bg-accent transition-colors text-sm"
              >
                Explain a concept
              </button>
              <button
                onclick={() => { inputMessage = "Create API documentation"; }}
                class="px-4 py-2 bg-card border border-border rounded-lg hover:bg-accent transition-colors text-sm"
              >
                Generate docs
              </button>
            </div>
          </div>
        {/if}
      </div>
    </div>

    <!-- Input Area -->
    <div class="border-t border-border bg-card px-4 py-4">
      <div class="max-w-4xl mx-auto">
        <div class="flex gap-3 items-end">
          <div class="flex-1 relative">
            <textarea
              bind:this={textareaElement}
              bind:value={inputMessage}
              onkeydown={handleKeydown}
              oninput={autoResizeTextarea}
              placeholder="Type your message..."
              disabled={isStreaming}
              class="w-full resize-none rounded-xl border border-border bg-background px-4 py-3 pr-12 focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent transition-all min-h-[52px] max-h-[200px] disabled:opacity-50"
              rows="1"
            />
            <div class="absolute right-2 bottom-2">
              {#if isStreaming}
                <button
                  onclick={stopStreaming}
                  class="p-2 bg-destructive text-destructive-foreground rounded-lg hover:bg-destructive/90 transition-colors"
                  title="Stop"
                >
                  <X class="w-4 h-4" />
                </button>
              {:else}
                <button
                  onclick={sendMessage}
                  disabled={!inputMessage.trim()}
                  class="p-2 bg-primary text-primary-foreground rounded-lg hover:bg-primary/90 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                  title="Send (Enter)"
                >
                  <Send class="w-4 h-4" />
                </button>
              {/if}
            </div>
          </div>
        </div>
        <div class="flex items-center justify-between mt-2">
          <p class="text-xs text-muted-foreground">
            Press Enter to send, Shift+Enter for new line
          </p>
          <p class="text-xs text-muted-foreground">
            {inputMessage.length} characters
          </p>
        </div>
      </div>
    </div>
  </div>

  <!-- Settings Modal -->
  {#if showSettings}
    <div class="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center z-50 p-4" onclick={() => showSettings = false}>
      <div class="bg-card rounded-xl shadow-2xl border border-border p-6 max-w-md w-full" onclick={(e) => e.stopPropagation()}>
        <div class="flex items-center justify-between mb-6">
          <h2 class="text-lg font-semibold">Chat Settings</h2>
          <button
            onclick={() => showSettings = false}
            class="p-1.5 hover:bg-accent rounded-lg transition-colors"
          >
            <X class="w-5 h-5" />
          </button>
        </div>
        
        <div class="space-y-4">
          <!-- Provider Selection -->
          <div>
            <label class="text-sm font-medium mb-2 block">AI Provider</label>
            <select
              bind:value={selectedProvider}
              class="w-full px-3 py-2 bg-background border border-border rounded-lg focus:outline-none focus:ring-2 focus:ring-primary"
              disabled={isLoadingModels}
            >
              {#each modelProviders as provider}
                <option value={provider.id}>{provider.name}</option>
              {/each}
            </select>
          </div>

          <!-- Model Selection -->
          <div>
            <label class="text-sm font-medium mb-2 block">Model</label>
            <select
              bind:value={selectedModel}
              class="w-full px-3 py-2 bg-background border border-border rounded-lg focus:outline-none focus:ring-2 focus:ring-primary"
              disabled={isLoadingModels || availableModels.length === 0}
            >
              {#each availableModels as model}
                <option value={model.id}>{model.name}</option>
              {/each}
            </select>
          </div>

          <!-- Temperature -->
          <div>
            <label class="text-sm font-medium mb-2 flex items-center justify-between">
              <span>Temperature</span>
              <span class="text-primary font-mono">{temperature.toFixed(1)}</span>
            </label>
            <input
              type="range"
              bind:value={temperature}
              min="0"
              max="2"
              step="0.1"
              class="w-full accent-primary"
            />
            <div class="flex justify-between text-xs text-muted-foreground mt-1">
              <span>Precise</span>
              <span>Creative</span>
            </div>
          </div>

          <!-- Max Tokens -->
          <div>
            <label class="text-sm font-medium mb-2 flex items-center justify-between">
              <span>Max Tokens</span>
              <span class="text-primary font-mono">{maxTokens}</span>
            </label>
            <input
              type="range"
              bind:value={maxTokens}
              min="100"
              max="4000"
              step="100"
              class="w-full accent-primary"
            />
            <div class="flex justify-between text-xs text-muted-foreground mt-1">
              <span>Short</span>
              <span>Long</span>
            </div>
          </div>
        </div>

        <div class="mt-6 flex justify-end gap-2">
          <button
            onclick={() => showSettings = false}
            class="px-4 py-2 text-sm border border-border rounded-lg hover:bg-accent transition-colors"
          >
            Cancel
          </button>
          <button
            onclick={() => { showSettings = false; saveConversations(); }}
            class="px-4 py-2 text-sm bg-primary text-primary-foreground rounded-lg hover:bg-primary/90 transition-colors"
          >
            Save Settings
          </button>
        </div>
      </div>
    </div>
  {/if}
</div>

<style>
  /* Custom scrollbar */
  .scrollbar-thin {
    scrollbar-width: thin;
    scrollbar-color: oklch(var(--muted)) transparent;
  }
  
  .scrollbar-thin::-webkit-scrollbar {
    width: 6px;
  }
  
  .scrollbar-thin::-webkit-scrollbar-track {
    background: transparent;
  }
  
  .scrollbar-thin::-webkit-scrollbar-thumb {
    background-color: oklch(var(--muted));
    border-radius: 3px;
  }
  
  .scrollbar-thin::-webkit-scrollbar-thumb:hover {
    background-color: oklch(var(--muted-foreground));
  }
</style>