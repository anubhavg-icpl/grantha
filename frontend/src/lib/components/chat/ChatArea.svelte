<script lang="ts">
	import { onMount } from 'svelte';
	import { chatState } from '$stores/chat';
	import { formatTime, parseMarkdown } from '$lib/utils';
	import type { ChatConversation, ChatMessage } from '$types/api';
	import { User, Bot, Copy, Check } from 'lucide-svelte';
	import Button from '../ui/button.svelte';
	import { copyToClipboard } from '$lib/utils';

	interface Props {
		conversation: ChatConversation;
	}

	let { conversation }: Props = $props();

	let messagesContainer: HTMLDivElement;
	let copiedMessageId: string | null = $state(null);

	// Auto-scroll to bottom when messages change
	$effect(() => {
		// Watch for changes in conversation messages
		conversation.messages;
		$chatState.streamingMessage;
		scrollToBottom();
	});

	function scrollToBottom() {
		if (messagesContainer) {
			messagesContainer.scrollTop = messagesContainer.scrollHeight;
		}
	}

	async function handleCopyMessage(message: ChatMessage, messageId: string) {
		const success = await copyToClipboard(message.content);
		if (success) {
			copiedMessageId = messageId;
			setTimeout(() => {
				copiedMessageId = null;
			}, 2000);
		}
	}

	function getMessageId(message: ChatMessage, index: number): string {
		return `${conversation.id}_${index}_${message.timestamp || 0}`;
	}
</script>

<div 
	bind:this={messagesContainer}
	class="flex-1 overflow-auto custom-scrollbar p-4 space-y-4"
>
	{#each conversation.messages as message, index}
		{@const messageId = getMessageId(message, index)}
		<div 
			class={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'} message-fade-in`}
		>
			<div 
				class={`group max-w-[80%] rounded-lg p-4 ${
					message.role === 'user' 
						? 'bg-primary text-primary-foreground ml-12' 
						: 'bg-muted text-muted-foreground mr-12'
				}`}
			>
				<!-- Message Header -->
				<div class="flex items-center space-x-2 mb-2">
					{#if message.role === 'user'}
						<User class="h-4 w-4" />
						<span class="text-sm font-medium">You</span>
					{:else}
						<Bot class="h-4 w-4" />
						<span class="text-sm font-medium">Assistant</span>
					{/if}
					
					{#if message.timestamp}
						<span class="text-xs opacity-70">
							{formatTime(message.timestamp)}
						</span>
					{/if}

					<!-- Copy button -->
					<Button
						size="icon"
						variant="ghost"
						class="h-6 w-6 opacity-0 group-hover:opacity-100 transition-opacity ml-auto"
						onclick={() => handleCopyMessage(message, messageId)}
						title="Copy message"
					>
						{#if copiedMessageId === messageId}
							<Check class="h-3 w-3 text-green-500" />
						{:else}
							<Copy class="h-3 w-3" />
						{/if}
					</Button>
				</div>

				<!-- Message Content -->
				<div class="text-sm whitespace-pre-wrap">
					{@html parseMarkdown(message.content)}
				</div>
			</div>
		</div>
	{/each}

	<!-- Streaming message -->
	{#if $chatState.isStreaming && $chatState.streamingMessage}
		<div class="flex justify-start message-fade-in">
			<div class="group max-w-[80%] rounded-lg p-4 bg-muted text-muted-foreground mr-12">
				<div class="flex items-center space-x-2 mb-2">
					<Bot class="h-4 w-4" />
					<span class="text-sm font-medium">Assistant</span>
					<span class="text-xs text-green-500">typing...</span>
					<div class="flex space-x-1">
						<div class="w-1 h-1 bg-current rounded-full animate-pulse"></div>
						<div class="w-1 h-1 bg-current rounded-full animate-pulse" style="animation-delay: 0.2s;"></div>
						<div class="w-1 h-1 bg-current rounded-full animate-pulse" style="animation-delay: 0.4s;"></div>
					</div>
				</div>
				
				<div class="text-sm whitespace-pre-wrap">
					{@html parseMarkdown($chatState.streamingMessage)}
					<span class="inline-block w-1 h-4 bg-current animate-pulse ml-1"></span>
				</div>
			</div>
		</div>
	{:else if $chatState.isStreaming}
		<div class="flex justify-start message-fade-in">
			<div class="group max-w-[80%] rounded-lg p-4 bg-muted text-muted-foreground mr-12">
				<div class="flex items-center space-x-2 mb-2">
					<Bot class="h-4 w-4" />
					<span class="text-sm font-medium">Assistant</span>
					<span class="text-xs text-blue-500">thinking...</span>
					<div class="flex space-x-1">
						<div class="w-1 h-1 bg-current rounded-full animate-pulse"></div>
						<div class="w-1 h-1 bg-current rounded-full animate-pulse" style="animation-delay: 0.2s;"></div>
						<div class="w-1 h-1 bg-current rounded-full animate-pulse" style="animation-delay: 0.4s;"></div>
					</div>
				</div>
				
				<div class="text-sm text-muted-foreground">
					Preparing response...
				</div>
			</div>
		</div>
	{/if}

	<!-- Error message -->
	{#if $chatState.error}
		<div class="flex justify-start message-fade-in">
			<div class="group max-w-[80%] rounded-lg p-4 bg-destructive/10 border border-destructive/20 text-destructive mr-12">
				<div class="flex items-center space-x-2 mb-2">
					<Bot class="h-4 w-4" />
					<span class="text-sm font-medium">Error</span>
				</div>
				
				<div class="text-sm">
					{$chatState.error}
				</div>
			</div>
		</div>
	{/if}

	<!-- Welcome message for empty conversations -->
	{#if conversation.messages.length === 0 && !$chatState.isStreaming && !$chatState.error}
		<div class="flex items-center justify-center h-full">
			<div class="text-center max-w-md">
				<Bot class="h-16 w-16 text-muted-foreground mx-auto mb-4" />
				<h3 class="text-lg font-semibold text-foreground mb-2">
					Start a conversation
				</h3>
				<p class="text-muted-foreground text-sm mb-4">
					Ask me anything! I can help with coding, writing, analysis, and much more.
				</p>
				<div class="grid grid-cols-1 gap-2 text-xs text-muted-foreground">
					<p>• Code explanations and debugging</p>
					<p>• Writing assistance and editing</p>
					<p>• Data analysis and insights</p>
					<p>• Problem-solving and brainstorming</p>
				</div>
			</div>
		</div>
	{/if}
</div>