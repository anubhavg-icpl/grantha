<script lang="ts">
	import { 
		MessageSquare, 
		Search, 
		Send,
		Copy,
		Download,
		Trash2,
		RefreshCw,
		Zap
	} from 'lucide-svelte';
	import Button from '$lib/components/ui/button.svelte';
	import Input from '$lib/components/ui/input.svelte';
	import LoadingSpinner from '$lib/components/ui/LoadingSpinner.svelte';
	import { apiClient } from '$lib/api/client';
	import type { SimpleRequest, RAGRequest } from '$lib/types/api';

	interface SimpleResult {
		id: string;
		type: 'chat' | 'rag';
		query: string;
		response?: string;
		context?: string;
		error?: string;
		createdAt: string;
	}

	let chatQuery = $state('');
	let ragQuery = $state('');
	let ragContext = $state('');
	let isLoadingChat = $state(false);
	let isLoadingRag = $state(false);
	let results = $state<SimpleResult[]>([]);

	const performSimpleChat = async () => {
		if (!chatQuery.trim() || isLoadingChat) return;

		isLoadingChat = true;
		const result: SimpleResult = {
			id: crypto.randomUUID(),
			type: 'chat',
			query: chatQuery.trim(),
			createdAt: new Date().toISOString()
		};

		results = [result, ...results];

		try {
			const request: SimpleRequest = {
				message: chatQuery.trim()
			};

			const response = await apiClient.simpleChat(request);
			result.response = response.response || response.message || 'No response received';
		} catch (error) {
			result.error = error instanceof Error ? error.message : 'Chat request failed';
		} finally {
			isLoadingChat = false;
			chatQuery = '';
			results = [...results]; // Trigger reactivity
		}
	};

	const performRAG = async () => {
		if (!ragQuery.trim() || isLoadingRag) return;

		isLoadingRag = true;
		const result: SimpleResult = {
			id: crypto.randomUUID(),
			type: 'rag',
			query: ragQuery.trim(),
			context: ragContext.trim() || undefined,
			createdAt: new Date().toISOString()
		};

		results = [result, ...results];

		try {
			const request: RAGRequest = {
				query: ragQuery.trim(),
				context: ragContext.trim() || undefined
			};

			const response = await apiClient.simpleRAG(request);
			result.response = response.response || response.answer || 'No response received';
		} catch (error) {
			result.error = error instanceof Error ? error.message : 'RAG request failed';
		} finally {
			isLoadingRag = false;
			ragQuery = '';
			ragContext = '';
			results = [...results]; // Trigger reactivity
		}
	};

	const copyToClipboard = async (text: string) => {
		try {
			await navigator.clipboard.writeText(text);
		} catch (err) {
			// Fallback for older browsers
			const textarea = document.createElement('textarea');
			textarea.value = text;
			document.body.appendChild(textarea);
			textarea.select();
			document.execCommand('copy');
			document.body.removeChild(textarea);
		}
	};

	const downloadResult = (result: SimpleResult) => {
		const data = {
			type: result.type,
			query: result.query,
			response: result.response,
			context: result.context,
			createdAt: result.createdAt
		};

		const blob = new Blob([JSON.stringify(data, null, 2)], {
			type: 'application/json'
		});
		const url = URL.createObjectURL(blob);
		const a = document.createElement('a');
		a.href = url;
		a.download = `${result.type}-result-${Date.now()}.json`;
		document.body.appendChild(a);
		a.click();
		document.body.removeChild(a);
		URL.revokeObjectURL(url);
	};

	const deleteResult = (id: string) => {
		results = results.filter(r => r.id !== id);
	};

	const clearAll = () => {
		results = [];
	};

	const handleChatKeyPress = (event: KeyboardEvent) => {
		if (event.key === 'Enter' && !event.shiftKey) {
			event.preventDefault();
			performSimpleChat();
		}
	};

	const handleRagKeyPress = (event: KeyboardEvent) => {
		if (event.key === 'Enter' && !event.shiftKey) {
			event.preventDefault();
			performRAG();
		}
	};
</script>

<svelte:head>
	<title>Simple Operations - Grantha</title>
</svelte:head>

<div class="space-y-6">
	<!-- Header -->
	<div>
		<h1 class="text-3xl font-bold text-foreground mb-2">Simple Operations</h1>
		<p class="text-muted-foreground">
			Quick AI interactions for simple chat and retrieval-augmented generation (RAG) queries.
		</p>
	</div>

	<!-- Quick Actions Grid -->
	<div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
		<!-- Simple Chat -->
		<div class="rounded-lg border bg-card p-6">
			<div class="flex items-center gap-2 mb-4">
				<MessageSquare class="w-5 h-5 text-primary" />
				<h2 class="text-lg font-semibold text-foreground">Simple Chat</h2>
			</div>
			
			<div class="space-y-4">
				<div>
					<label for="chat-input" class="text-sm font-medium text-foreground block mb-2">
						Message
					</label>
					<Input
						id="chat-input"
						bind:value={chatQuery}
						placeholder="Ask anything..."
						on:keypress={handleChatKeyPress}
						disabled={isLoadingChat}
						class="w-full"
					/>
				</div>
				
				<Button 
					on:click={performSimpleChat}
					disabled={!chatQuery.trim() || isLoadingChat}
					class="w-full"
				>
					{#if isLoadingChat}
						<LoadingSpinner size="sm" class="mr-2" />
					{:else}
						<Send class="w-4 h-4 mr-2" />
					{/if}
					Send Message
				</Button>
			</div>
		</div>

		<!-- RAG Query -->
		<div class="rounded-lg border bg-card p-6">
			<div class="flex items-center gap-2 mb-4">
				<Search class="w-5 h-5 text-primary" />
				<h2 class="text-lg font-semibold text-foreground">RAG Query</h2>
			</div>
			
			<div class="space-y-4">
				<div>
					<label for="rag-context" class="text-sm font-medium text-foreground block mb-2">
						Context (Optional)
					</label>
					<textarea
						id="rag-context"
						bind:value={ragContext}
						placeholder="Provide context or documents for the query..."
						class="w-full min-h-[80px] px-3 py-2 text-sm rounded-md border border-input bg-background placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50 resize-none"
						disabled={isLoadingRag}
					></textarea>
				</div>
				
				<div>
					<label for="rag-query" class="text-sm font-medium text-foreground block mb-2">
						Query
					</label>
					<Input
						id="rag-query"
						bind:value={ragQuery}
						placeholder="What would you like to know?"
						on:keypress={handleRagKeyPress}
						disabled={isLoadingRag}
						class="w-full"
					/>
				</div>
				
				<Button 
					on:click={performRAG}
					disabled={!ragQuery.trim() || isLoadingRag}
					class="w-full"
				>
					{#if isLoadingRag}
						<LoadingSpinner size="sm" class="mr-2" />
					{:else}
						<Zap class="w-4 h-4 mr-2" />
					{/if}
					Execute RAG
				</Button>
			</div>
		</div>
	</div>

	<!-- Results -->
	{#if results.length > 0}
		<div class="space-y-4">
			<div class="flex items-center justify-between">
				<h2 class="text-xl font-semibold text-foreground">Results</h2>
				<Button variant="outline" size="sm" on:click={clearAll}>
					<Trash2 class="w-4 h-4 mr-2" />
					Clear All
				</Button>
			</div>

			<div class="space-y-4">
				{#each results as result (result.id)}
					<div class="rounded-lg border bg-card p-6">
						<!-- Result Header -->
						<div class="flex items-start justify-between mb-4">
							<div class="flex items-center gap-2">
								{#if result.type === 'chat'}
									<MessageSquare class="w-4 h-4 text-blue-500" />
									<span class="text-sm font-medium text-foreground">Simple Chat</span>
								{:else}
									<Search class="w-4 h-4 text-green-500" />
									<span class="text-sm font-medium text-foreground">RAG Query</span>
								{/if}
								<span class="text-xs text-muted-foreground">
									{new Date(result.createdAt).toLocaleString()}
								</span>
							</div>
							
							<div class="flex items-center gap-2">
								{#if result.response}
									<Button
										variant="ghost"
										size="sm"
										on:click={() => copyToClipboard(result.response || '')}
									>
										<Copy class="w-4 h-4" />
									</Button>
									<Button
										variant="ghost"
										size="sm"
										on:click={() => downloadResult(result)}
									>
										<Download class="w-4 h-4" />
									</Button>
								{/if}
								<Button
									variant="ghost"
									size="sm"
									on:click={() => deleteResult(result.id)}
								>
									<Trash2 class="w-4 h-4" />
								</Button>
							</div>
						</div>

						<!-- Query -->
						<div class="mb-4">
							<h4 class="text-sm font-medium text-foreground mb-2">Query:</h4>
							<div class="bg-muted rounded-lg p-3">
								<p class="text-sm text-foreground">{result.query}</p>
							</div>
						</div>

						<!-- Context (for RAG) -->
						{#if result.context}
							<div class="mb-4">
								<h4 class="text-sm font-medium text-foreground mb-2">Context:</h4>
								<div class="bg-muted rounded-lg p-3">
									<p class="text-sm text-muted-foreground whitespace-pre-wrap">{result.context}</p>
								</div>
							</div>
						{/if}

						<!-- Response or Error -->
						{#if result.error}
							<div class="border-destructive/20 bg-destructive/10 rounded-lg p-3">
								<h4 class="text-sm font-medium text-destructive mb-2">Error:</h4>
								<p class="text-sm text-destructive">{result.error}</p>
							</div>
						{:else if result.response}
							<div>
								<h4 class="text-sm font-medium text-foreground mb-2">Response:</h4>
								<div class="bg-accent/10 border border-accent/20 rounded-lg p-4">
									<p class="text-sm text-foreground whitespace-pre-wrap">{result.response}</p>
								</div>
							</div>
						{:else}
							<div class="flex items-center justify-center py-4">
								<LoadingSpinner size="sm" />
								<span class="ml-2 text-sm text-muted-foreground">Processing...</span>
							</div>
						{/if}
					</div>
				{/each}
			</div>
		</div>
	{:else}
		<div class="text-center py-12">
			<Zap class="w-12 h-12 text-muted-foreground mx-auto mb-4" />
			<h3 class="text-lg font-medium text-foreground mb-2">No Operations Yet</h3>
			<p class="text-muted-foreground">
				Use the simple chat or RAG query tools above to get started.
			</p>
		</div>
	{/if}
</div>