<script lang="ts">
	import { onMount } from 'svelte';
	import { 
		Search, 
		Download, 
		FileText, 
		ExternalLink,
		Clock,
		Brain,
		Lightbulb,
		CheckCircle,
		AlertCircle,
		Loader2
	} from 'lucide-svelte';
	import Button from '$lib/components/ui/button.svelte';
	import Input from '$lib/components/ui/input.svelte';
	import LoadingSpinner from '$lib/components/ui/LoadingSpinner.svelte';
	import { apiClient } from '$lib/api/client';
	import type { DeepResearchRequest } from '$lib/types/api';

	interface ResearchResult {
		id: string;
		query: string;
		status: 'running' | 'completed' | 'error';
		results?: {
			summary: string;
			sources: Array<{
				title: string;
				url: string;
				snippet: string;
			}>;
			insights: string[];
		};
		error?: string;
		createdAt: string;
		completedAt?: string;
	}

	let query = $state('');
	let isLoading = $state(false);
	let results = $state<ResearchResult[]>([]);
	let currentResearch = $state<ResearchResult | null>(null);

	const startResearch = async () => {
		if (!query.trim() || isLoading) return;

		isLoading = true;
		const research: ResearchResult = {
			id: crypto.randomUUID(),
			query: query.trim(),
			status: 'running',
			createdAt: new Date().toISOString()
		};

		results = [research, ...results];
		currentResearch = research;

		try {
			const request: DeepResearchRequest = {
				query: query.trim(),
				repo_url: 'https://github.com/example/repo', // Default repo for research context
				language: 'en'
			};

			const response = await apiClient.deepResearch(request);
			
			// Update the research result based on actual API response
			if (response.status === 'success') {
				research.status = 'completed';
				research.results = {
					summary: response.results || 'Research completed successfully',
					sources: [], // Backend doesn't provide sources yet
					insights: response.results ? [response.results] : []
				};
			} else {
				research.status = 'error';
				research.error = response.message || 'Research failed';
			}
			
			research.completedAt = new Date().toISOString();
			results = [...results]; // Trigger reactivity
		} catch (error) {
			research.status = 'error';
			research.error = error instanceof Error ? error.message : 'Research failed';
			results = [...results]; // Trigger reactivity
		} finally {
			isLoading = false;
			query = '';
		}
	};

	const handleKeyPress = (event: KeyboardEvent) => {
		if (event.key === 'Enter' && !event.shiftKey) {
			event.preventDefault();
			startResearch();
		}
	};

	const exportResults = (research: ResearchResult) => {
		if (!research.results) return;

		const exportData = {
			query: research.query,
			summary: research.results.summary,
			sources: research.results.sources,
			insights: research.results.insights,
			generatedAt: new Date().toISOString()
		};

		const blob = new Blob([JSON.stringify(exportData, null, 2)], {
			type: 'application/json'
		});
		const url = URL.createObjectURL(blob);
		const a = document.createElement('a');
		a.href = url;
		a.download = `research-${research.query.replace(/[^a-z0-9]/gi, '_').toLowerCase()}.json`;
		document.body.appendChild(a);
		a.click();
		document.body.removeChild(a);
		URL.revokeObjectURL(url);
	};

	onMount(() => {
		// Load any cached research results from localStorage
		const cached = localStorage.getItem('grantha-research-results');
		if (cached) {
			try {
				results = JSON.parse(cached);
			} catch (e) {
				console.warn('Failed to load cached research results');
			}
		}
	});

	// Save results to localStorage whenever they change
	$effect(() => {
		localStorage.setItem('grantha-research-results', JSON.stringify(results));
	});
</script>

<svelte:head>
	<title>Research Tools - Grantha</title>
</svelte:head>

<div class="space-y-6">
	<!-- Header -->
	<div>
		<h1 class="text-3xl font-bold text-foreground mb-2">Research Tools</h1>
		<p class="text-muted-foreground">
			Conduct deep research on any topic with AI-powered analysis and source compilation.
		</p>
	</div>

	<!-- Research Input -->
	<div class="rounded-lg border bg-card p-6">
		<div class="space-y-4">
			<div>
				<label for="research-query" class="text-sm font-medium text-foreground block mb-2">
					Research Query
				</label>
				<div class="flex gap-2">
					<Input
						id="research-query"
						bind:value={query}
						placeholder="Enter your research topic or question..."
						onkeypress={handleKeyPress}
						class="flex-1"
						disabled={isLoading}
					/>
					<Button 
						onclick={startResearch}
						disabled={!query.trim() || isLoading}
						class="px-6"
					>
						{#if isLoading}
							<Loader2 class="w-4 h-4 mr-2 animate-spin" />
						{:else}
							<Search class="w-4 h-4 mr-2" />
						{/if}
						Research
					</Button>
				</div>
			</div>

			{#if isLoading}
				<div class="flex items-center gap-2 text-sm text-muted-foreground">
					<LoadingSpinner size="sm" />
					Conducting deep research...
				</div>
			{/if}
		</div>
	</div>

	<!-- Research Results -->
	{#if results.length > 0}
		<div class="space-y-6">
			<h2 class="text-xl font-semibold text-foreground">Research Results</h2>
			
			{#each results as research (research.id)}
				<div class="rounded-lg border bg-card p-6">
					<!-- Research Header -->
					<div class="flex items-start justify-between mb-4">
						<div class="flex-1">
							<h3 class="font-semibold text-foreground mb-1">
								{research.query}
							</h3>
							<div class="flex items-center gap-4 text-sm text-muted-foreground">
								<div class="flex items-center gap-1">
									<Clock class="w-3 h-3" />
									{new Date(research.createdAt).toLocaleString()}
								</div>
								<div class="flex items-center gap-1">
									{#if research.status === 'running'}
										<Loader2 class="w-3 h-3 animate-spin" />
										Running...
									{:else if research.status === 'completed'}
										<CheckCircle class="w-3 h-3 text-green-500" />
										Completed
									{:else}
										<AlertCircle class="w-3 h-3 text-destructive" />
										Error
									{/if}
								</div>
							</div>
						</div>
						
						{#if research.status === 'completed' && research.results}
							<Button
								variant="outline"
								size="sm"
								onclick={() => exportResults(research)}
							>
								<Download class="w-4 h-4 mr-2" />
								Export
							</Button>
						{/if}
					</div>

					<!-- Results Content -->
					{#if research.status === 'running'}
						<div class="flex items-center justify-center py-8">
							<LoadingSpinner text="Analyzing sources and generating insights..." />
						</div>
					{:else if research.status === 'error'}
						<div class="rounded-lg border-destructive/20 bg-destructive/10 p-4">
							<div class="flex items-center gap-2 mb-2">
								<AlertCircle class="w-4 h-4 text-destructive" />
								<span class="font-medium text-destructive">Research Failed</span>
							</div>
							<p class="text-sm text-destructive">{research.error}</p>
						</div>
					{:else if research.results}
						<div class="space-y-6">
							<!-- Summary -->
							<div>
								<h4 class="font-medium text-foreground mb-3 flex items-center gap-2">
									<Brain class="w-4 h-4" />
									Summary
								</h4>
								<div class="bg-muted rounded-lg p-4">
									<p class="text-sm text-foreground whitespace-pre-wrap">
										{research.results.summary}
									</p>
								</div>
							</div>

							<!-- Key Insights -->
							{#if research.results.insights.length > 0}
								<div>
									<h4 class="font-medium text-foreground mb-3 flex items-center gap-2">
										<Lightbulb class="w-4 h-4" />
										Key Insights
									</h4>
									<ul class="space-y-2">
										{#each research.results.insights as insight}
											<li class="flex items-start gap-2 text-sm">
												<div class="w-1.5 h-1.5 rounded-full bg-primary mt-2 flex-shrink-0"></div>
												<span class="text-foreground">{insight}</span>
											</li>
										{/each}
									</ul>
								</div>
							{/if}

							<!-- Sources -->
							{#if research.results.sources.length > 0}
								<div>
									<h4 class="font-medium text-foreground mb-3 flex items-center gap-2">
										<FileText class="w-4 h-4" />
										Sources ({research.results.sources.length})
									</h4>
									<div class="space-y-3">
										{#each research.results.sources as source}
											<div class="border rounded-lg p-4">
												<div class="flex items-start justify-between mb-2">
													<h5 class="font-medium text-foreground text-sm">
														{source.title}
													</h5>
													<a
														href={source.url}
														target="_blank"
														rel="noopener noreferrer"
														class="flex items-center gap-1 text-xs text-muted-foreground hover:text-foreground"
													>
														<ExternalLink class="w-3 h-3" />
														Open
													</a>
												</div>
												<p class="text-xs text-muted-foreground mb-2 break-all">
													{source.url}
												</p>
												<p class="text-sm text-foreground">
													{source.snippet}
												</p>
											</div>
										{/each}
									</div>
								</div>
							{/if}
						</div>
					{/if}
				</div>
			{/each}
		</div>
	{:else}
		<div class="text-center py-12">
			<Search class="w-12 h-12 text-muted-foreground mx-auto mb-4" />
			<h3 class="text-lg font-medium text-foreground mb-2">No Research Yet</h3>
			<p class="text-muted-foreground">
				Enter a topic or question above to start your first research session.
			</p>
		</div>
	{/if}
</div>