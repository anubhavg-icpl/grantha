<script lang="ts">
	import { onMount } from 'svelte';
	import { 
		chatState, 
		chatActions, 
		activeConversation, 
		canSendMessage 
	} from '$stores/chat';
	import { modelsState, effectiveModel, currentProvider } from '$stores/models';
	import ChatSidebar from '$lib/components/chat/ChatSidebar.svelte';
	import ChatArea from '$lib/components/chat/ChatArea.svelte';
	import ChatInput from '$lib/components/chat/ChatInput.svelte';
	import ModelSelector from '$lib/components/models/ModelSelector.svelte';
	import Button from '$lib/components/ui/button.svelte';
	import LoadingSpinner from '$lib/components/ui/LoadingSpinner.svelte';
	import { MessageSquare, Plus, Settings } from 'lucide-svelte';

	let showSidebar = $state(true);
	let showSettings = $state(false);

	onMount(() => {
		// Auto-create first conversation if none exist
		if ($chatState.conversations.length === 0) {
			chatActions.createConversation();
		}
	});

	function handleNewChat() {
		chatActions.createConversation();
	}

	function handleSendMessage(event: CustomEvent<{ message: string }>) {
		chatActions.sendMessage(event.detail.message, true);
	}

	function toggleSidebar() {
		showSidebar = !showSidebar;
	}
</script>

<svelte:head>
	<title>Chat - Grantha</title>
</svelte:head>

<div class="flex h-[calc(100vh-8rem)] rounded-lg border bg-card overflow-hidden">
	<!-- Chat Sidebar -->
	{#if showSidebar}
		<div class="w-64 border-r bg-card">
			<div class="p-4 border-b">
				<div class="flex items-center justify-between mb-4">
					<h2 class="font-semibold text-foreground">Conversations</h2>
					<Button
						size="icon"
						variant="ghost"
						on:click={handleNewChat}
						title="New conversation"
					>
						<Plus class="h-4 w-4" />
					</Button>
				</div>
				
				<!-- Model selector -->
				<div class="space-y-2">
					<Button
						size="sm"
						variant="outline"
						class="w-full justify-between text-xs"
						on:click={() => showSettings = !showSettings}
					>
						<span class="truncate">
							{$effectiveModel?.name || 'Select model'}
						</span>
						<Settings class="h-3 w-3" />
					</Button>
					
					{#if showSettings}
						<div class="p-2 border rounded-lg bg-muted/50">
							<ModelSelector />
						</div>
					{/if}
				</div>
			</div>
			
			<ChatSidebar />
		</div>
	{/if}

	<!-- Main Chat Area -->
	<div class="flex-1 flex flex-col">
		<!-- Chat Header -->
		<div class="p-4 border-b">
			<div class="flex items-center justify-between">
				<div class="flex items-center space-x-3">
					{#if !showSidebar}
						<Button
							size="icon"
							variant="ghost"
							on:click={toggleSidebar}
							title="Show conversations"
						>
							<MessageSquare class="h-4 w-4" />
						</Button>
					{/if}
					
					<div>
						<h1 class="font-semibold text-foreground">
							{$activeConversation?.title || 'New Chat'}
						</h1>
						<p class="text-sm text-muted-foreground">
							{#if $currentProvider && $effectiveModel}
								{$currentProvider.name} • {$effectiveModel.name}
							{:else if $modelsState.isLoading}
								Loading models...
							{:else}
								No model selected
							{/if}
						</p>
					</div>
				</div>
				
				{#if showSidebar}
					<Button
						size="icon"
						variant="ghost"
						on:click={toggleSidebar}
						title="Hide conversations"
					>
						<MessageSquare class="h-4 w-4" />
					</Button>
				{/if}
			</div>
		</div>

		<!-- Chat Messages -->
		<div class="flex-1 overflow-hidden">
			{#if $activeConversation}
				<ChatArea conversation={$activeConversation} />
			{:else}
				<div class="flex items-center justify-center h-full">
					<div class="text-center">
						<MessageSquare class="h-12 w-12 text-muted-foreground mx-auto mb-4" />
						<h3 class="text-lg font-semibold text-foreground mb-2">
							No conversation selected
						</h3>
						<p class="text-muted-foreground mb-4">
							Start a new conversation to begin chatting
						</p>
						<Button on:click={handleNewChat}>
							<Plus class="mr-2 h-4 w-4" />
							New Chat
						</Button>
					</div>
				</div>
			{/if}
		</div>

		<!-- Chat Input -->
		{#if $activeConversation}
			<div class="p-4 border-t">
				<ChatInput
					disabled={!$canSendMessage || !$effectiveModel}
					loading={$chatState.isLoading || $chatState.isStreaming}
					on:send={handleSendMessage}
				/>
				
				{#if !$effectiveModel}
					<p class="text-sm text-muted-foreground mt-2">
						Please select a model to start chatting
					</p>
				{/if}
			</div>
		{/if}
	</div>
</div>

<!-- Loading overlay -->
{#if $modelsState.isLoading}
	<div class="fixed inset-0 bg-background/50 flex items-center justify-center z-50">
		<LoadingSpinner size="lg" text="Loading chat interface..." />
	</div>
{/if}