<script lang="ts">
	import { createEventDispatcher } from 'svelte';
	import { chatActions, chatState } from '$stores/chat';
	import Button from '../ui/button.svelte';
	import { Send, Square, Paperclip } from 'lucide-svelte';
	import { cn } from '$lib/utils';

	interface Props {
		disabled?: boolean;
		loading?: boolean;
		placeholder?: string;
		class?: string;
	}

	let { 
		disabled = false,
		loading = false,
		placeholder = 'Type your message...',
		class: className = ''
	}: Props = $props();

	const dispatch = createEventDispatcher<{
		send: { message: string };
	}>();

	let message = $state('');
	let textareaElement: HTMLTextAreaElement;

	// Generate unique ID for accessibility
	const textareaId = `chat-input-${crypto.randomUUID()}`;

	function handleSubmit() {
		const trimmedMessage = message.trim();
		if (!trimmedMessage || disabled || loading) return;

		dispatch('send', { message: trimmedMessage });
		message = '';
		adjustTextareaHeight();
	}

	function handleKeyDown(event: KeyboardEvent) {
		if (event.key === 'Enter' && !event.shiftKey) {
			event.preventDefault();
			handleSubmit();
		}
	}

	function adjustTextareaHeight() {
		if (textareaElement) {
			textareaElement.style.height = 'auto';
			textareaElement.style.height = Math.min(textareaElement.scrollHeight, 120) + 'px';
		}
	}

	function handleInput() {
		adjustTextareaHeight();
	}

	function stopStreaming() {
		chatActions.stopStreaming();
	}

	// Auto-resize textarea on mount
	$effect(() => {
		if (textareaElement) {
			adjustTextareaHeight();
		}
	});
</script>

<div class={cn('space-y-3', className)}>
	<!-- Error display -->
	{#if $chatState.error}
		<div class="rounded-lg bg-destructive/10 border border-destructive/20 p-3">
			<p class="text-sm text-destructive">{$chatState.error}</p>
			<Button
				variant="ghost"
				size="sm"
				class="mt-2 text-destructive hover:text-destructive"
				onclick={chatActions.clearError}
			>
				Dismiss
			</Button>
		</div>
	{/if}

	<!-- Input area -->
	<div class="relative rounded-lg border border-input bg-background focus-within:ring-1 focus-within:ring-ring">
		<label for={textareaId} class="sr-only">
			Type your message
		</label>
		<textarea
			id={textareaId}
			bind:this={textareaElement}
			bind:value={message}
			onkeydown={handleKeyDown}
			oninput={handleInput}
			{placeholder}
			{disabled}
			rows="1"
			aria-label="Type your message"
			aria-describedby="chat-hints"
			class="w-full resize-none bg-transparent px-3 py-3 pr-20 text-sm placeholder:text-muted-foreground focus:outline-none disabled:cursor-not-allowed disabled:opacity-50"
			style="min-height: 44px; max-height: 120px;"
		></textarea>

		<!-- Action buttons -->
		<div class="absolute right-2 bottom-2 flex items-center space-x-1">
			<!-- File attachment button (placeholder) -->
			<Button
				size="icon"
				variant="ghost"
				class="h-8 w-8"
				disabled={true}
				title="Attach file (coming soon)"
			>
				<Paperclip class="h-4 w-4" />
			</Button>

			<!-- Send/Stop button -->
			{#if $chatState.isStreaming}
				<Button
					size="icon"
					variant="destructive"
					class="h-8 w-8"
					onclick={stopStreaming}
					title="Stop generation"
				>
					<Square class="h-4 w-4" />
				</Button>
			{:else}
				<Button
					size="icon"
					variant="default"
					class="h-8 w-8"
					{disabled}
					loading={loading && !$chatState.isStreaming}
					onclick={handleSubmit}
					title="Send message"
				>
					<Send class="h-4 w-4" />
				</Button>
			{/if}
		</div>
	</div>

	<!-- Hints -->
	<div id="chat-hints" class="flex items-center justify-between text-xs text-muted-foreground">
		<div class="flex items-center space-x-4">
			<span>Press Enter to send, Shift+Enter for new line</span>
			{#if $chatState.isStreaming}
				<span class="text-orange-600">• Streaming response...</span>
			{/if}
		</div>
		
		<div class="text-right">
			{message.length}/4000
		</div>
	</div>
</div>