<script lang="ts">
	import { BookOpen, Plus, Search, FileText, ExternalLink, AlertCircle, CheckCircle } from 'lucide-svelte';
	import Button from '$lib/components/ui/button.svelte';
	import Input from '$lib/components/ui/input.svelte';
	import LoadingSpinner from '$lib/components/ui/LoadingSpinner.svelte';
	import { modelsState, modelsActions } from '$lib/stores/models';
	import { apiClient } from '$lib/api/client';
	import type { WikiGenerationRequest, WikiStructureModel } from '$lib/types/api';
	import { onMount } from 'svelte';
	import { page } from '$app/stores';
	import { get } from 'svelte/store';

	let repoUrl = $state('');
	let searchQuery = $state('');
	let isGenerating = $state(false);
	let generationResult = $state<{status: string; wiki_structure?: WikiStructureModel; error?: string; provider?: string; model?: string} | null>(null);
	let generationError = $state<string | null>(null);
	let recentWikis = $state<WikiStructureModel[]>([]);

	onMount(() => {
		// Check URL parameters
		const pageStore = get(page);
		const searchParams = pageStore.url.searchParams;
		
		// Handle URL parameters: owner, repo, type, language
		const owner = searchParams.get('owner');
		const repo = searchParams.get('repo');
		const type = searchParams.get('type') || 'github';
		const language = searchParams.get('language') || 'en';
		
		if (owner && repo) {
			// Construct the repository URL from parameters
			if (type === 'github') {
				repoUrl = `https://github.com/${owner}/${repo}`;
			} else if (type === 'gitlab') {
				repoUrl = `https://gitlab.com/${owner}/${repo}`;
			} else if (type === 'bitbucket') {
				repoUrl = `https://bitbucket.org/${owner}/${repo}`;
			}
			
			// Auto-generate wiki if URL is provided
			if (repoUrl) {
				handleGenerateWiki();
			}
		}
		
		// Load model config if not already loaded
		if (!$modelsState.config) {
			modelsActions.loadConfig();
		}
		
		// Load saved wikis from localStorage
		loadSavedWikis();
	});

	function loadSavedWikis() {
		try {
			const saved = localStorage.getItem('grantha-generated-wikis');
			if (saved) {
				recentWikis = JSON.parse(saved);
			}
		} catch (error) {
			console.error('Failed to load saved wikis:', error);
		}
	}

	function saveWikiToLocal(wiki: WikiStructureModel) {
		try {
			recentWikis = [wiki, ...recentWikis.slice(0, 9)]; // Keep max 10 wikis
			localStorage.setItem('grantha-generated-wikis', JSON.stringify(recentWikis));
		} catch (error) {
			console.error('Failed to save wiki:', error);
		}
	}

	async function handleGenerateWiki() {
		if (!repoUrl.trim() || isGenerating) return;
		
		isGenerating = true;
		generationError = null;
		generationResult = null;

		try {
			const { provider, model } = modelsActions.getCurrentSelection();
			
			const request: WikiGenerationRequest = {
				repo_url: repoUrl.trim(),
				language: 'en',
				provider: provider || undefined,
				model: model || undefined
			};

			const result = await apiClient.generateWiki(request);
			
			if (result.status === 'error') {
				generationError = result.message || 'Wiki generation failed';
			} else {
				generationResult = result;
				
				// Save to local storage if successful
				if (result.wiki_structure) {
					saveWikiToLocal({
						...result.wiki_structure,
						repo_url: repoUrl.trim(),
						generated_at: Date.now()
					});
				}
			}
			
		} catch (error) {
			generationError = error instanceof Error ? error.message : 'Failed to generate wiki';
			console.error('Wiki generation error:', error);
		} finally {
			isGenerating = false;
		}
	}

	function clearResult() {
		generationResult = null;
		generationError = null;
	}

	function isValidUrl(url: string): boolean {
		try {
			new URL(url);
			return url.includes('github.com') || url.includes('gitlab.com') || url.includes('bitbucket.org');
		} catch {
			return false;
		}
	}

	const filteredWikis = $derived(recentWikis.filter(wiki => 
		!searchQuery || 
		wiki.title?.toLowerCase().includes(searchQuery.toLowerCase()) ||
		wiki.description?.toLowerCase().includes(searchQuery.toLowerCase())
	));
</script>

<svelte:head>
	<title>Wiki - Grantha</title>
</svelte:head>

<div class="space-y-8">
	<!-- Header -->
	<div class="text-center">
		<h1 class="text-4xl font-bold text-foreground mb-4">
			Wiki Documentation
		</h1>
		<p class="text-lg text-muted-foreground max-w-2xl mx-auto">
			Generate comprehensive documentation for any repository using AI. 
			Create wikis, API docs, and technical guides automatically.
		</p>
	</div>

	<!-- Wiki Generation -->
	<div class="max-w-2xl mx-auto">
		<div class="rounded-lg border bg-card p-6">
			<div class="flex items-center mb-4">
				<Plus class="mr-2 h-5 w-5 text-primary" />
				<h2 class="text-lg font-semibold">Generate New Wiki</h2>
			</div>
			
			<div class="space-y-4">
				<div>
					<label for="repo-url" class="block text-sm font-medium mb-2">
						Repository URL
					</label>
					<Input
						id="repo-url"
						type="url"
						placeholder="https://github.com/user/repo"
						bind:value={repoUrl}
						disabled={isGenerating}
						class={!isValidUrl(repoUrl) && repoUrl.trim() ? 'border-destructive' : ''}
					/>
					{#if repoUrl.trim() && !isValidUrl(repoUrl)}
						<p class="text-sm text-destructive mt-1">
							Please enter a valid GitHub, GitLab, or Bitbucket repository URL
						</p>
					{/if}
				</div>
				
				{#if $modelsState.error}
					<div class="bg-destructive/10 border border-destructive/20 rounded-lg p-3">
						<div class="flex items-center gap-2">
							<AlertCircle class="h-4 w-4 text-destructive" />
							<p class="text-sm text-destructive">Model configuration error: {$modelsState.error}</p>
						</div>
					</div>
				{/if}
				
				{#if generationError}
					<div class="bg-destructive/10 border border-destructive/20 rounded-lg p-3">
						<div class="flex items-center justify-between">
							<div class="flex items-center gap-2">
								<AlertCircle class="h-4 w-4 text-destructive" />
								<p class="text-sm text-destructive">{generationError}</p>
							</div>
							<Button variant="ghost" size="sm" onclick={clearResult}>
								×
							</Button>
						</div>
					</div>
				{/if}
				
				{#if generationResult && generationResult.status === 'success' && generationResult.wiki_structure}
					<div class="bg-success/10 border border-success/20 rounded-lg p-4 space-y-3">
						<div class="flex items-center justify-between">
							<div class="flex items-center gap-2">
								<CheckCircle class="h-4 w-4 text-success" />
								<p class="text-sm font-medium text-success">Wiki generated successfully!</p>
							</div>
							<Button variant="ghost" size="sm" onclick={clearResult}>
								×
							</Button>
						</div>
						<div class="text-sm space-y-2">
							<p><strong>Title:</strong> {generationResult.wiki_structure.title}</p>
							<p><strong>Description:</strong> {generationResult.wiki_structure.description}</p>
							<p><strong>Pages:</strong> {generationResult.wiki_structure.pages?.length || 0}</p>
							<p><strong>Provider:</strong> {generationResult.provider} • <strong>Model:</strong> {generationResult.model}</p>
						</div>
					</div>
				{/if}
				
				<Button
					class="w-full"
					disabled={!repoUrl.trim() || !isValidUrl(repoUrl) || isGenerating || $modelsState.isLoading}
					onclick={handleGenerateWiki}
				>
					{#if isGenerating}
						<LoadingSpinner size="sm" class="mr-2" />
						Generating Wiki...
					{:else if $modelsState.isLoading}
						<LoadingSpinner size="sm" class="mr-2" />
						Loading Models...
					{:else}
						<BookOpen class="mr-2 h-4 w-4" />
						Generate Wiki Documentation
					{/if}
				</Button>
			</div>
		</div>
	</div>

	<!-- Recent Wikis -->
	<div>
		<div class="flex items-center justify-between mb-6">
			<h2 class="text-2xl font-semibold text-foreground">Recent Wikis</h2>
			
			<div class="flex items-center space-x-3">
				<div class="relative">
					<Search class="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-muted-foreground" aria-hidden="true" />
					<Input
						id="wiki-search"
						placeholder="Search wikis..."
						bind:value={searchQuery}
						label="Search wikis"
						hideLabel={true}
						aria-label="Search wikis"
						class="pl-10 w-64"
					/>
				</div>
			</div>
		</div>

		<!-- Wiki Grid -->
		{#if filteredWikis.length > 0}
			<div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
				{#each filteredWikis as wiki (wiki.id || wiki.title)}
					<div class="rounded-lg border bg-card p-6 hover:shadow-md transition-shadow">
						<div class="flex items-start justify-between mb-3">
							<div class="flex items-center">
								<BookOpen class="h-5 w-5 text-primary mr-2" />
								<h3 class="font-semibold text-foreground truncate">{wiki.title}</h3>
							</div>
							{#if wiki.repo_url}
								<Button 
									size="icon" 
									variant="ghost" 
									class="h-8 w-8"
									onclick={() => window.open(wiki.repo_url, '_blank')}
								>
									<ExternalLink class="h-4 w-4" />
								</Button>
							{/if}
						</div>
						
						<p class="text-sm text-muted-foreground mb-4 line-clamp-3">
							{wiki.description || 'No description available'}
						</p>
						
						<div class="flex items-center justify-between text-xs text-muted-foreground">
							<span>
								{#if wiki.generated_at}
									Generated {new Date(wiki.generated_at).toLocaleDateString()}
								{:else}
									Recent
								{/if}
							</span>
							<span>{wiki.pages?.length || 0} pages</span>
						</div>
					</div>
				{/each}
			</div>
		{:else if searchQuery.length > 0}
			<!-- Empty state when search has no results -->
			<div class="text-center py-12">
				<Search class="h-12 w-12 text-muted-foreground mx-auto mb-4" />
				<h3 class="text-lg font-semibold text-foreground mb-2">No wikis found</h3>
				<p class="text-muted-foreground">
					No wikis match your search query "{searchQuery}"
				</p>
			</div>
		{:else if recentWikis.length === 0}
			<!-- Empty state when no wikis exist -->
			<div class="text-center py-12">
				<BookOpen class="h-12 w-12 text-muted-foreground mx-auto mb-4" />
				<h3 class="text-lg font-semibold text-foreground mb-2">No wikis yet</h3>
				<p class="text-muted-foreground">
					Generate your first wiki using the form above
				</p>
			</div>
		{/if}
	</div>

	<!-- Features -->
	<div class="rounded-lg border bg-card p-6">
		<h3 class="text-lg font-semibold text-foreground mb-4">Wiki Features</h3>
		<div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
			<div class="flex items-start space-x-3">
				<FileText class="h-5 w-5 text-primary mt-0.5" />
				<div>
					<h4 class="font-medium text-foreground">Auto-Generated Content</h4>
					<p class="text-sm text-muted-foreground">
						AI analyzes your code to create comprehensive documentation
					</p>
				</div>
			</div>
			
			<div class="flex items-start space-x-3">
				<BookOpen class="h-5 w-5 text-primary mt-0.5" />
				<div>
					<h4 class="font-medium text-foreground">Multiple Formats</h4>
					<p class="text-sm text-muted-foreground">
						Export as Markdown, HTML, or JSON for various use cases
					</p>
				</div>
			</div>
			
			<div class="flex items-start space-x-3">
				<Search class="h-5 w-5 text-primary mt-0.5" />
				<div>
					<h4 class="font-medium text-foreground">Smart Organization</h4>
					<p class="text-sm text-muted-foreground">
						Intelligently organizes content by importance and relationships
					</p>
				</div>
			</div>
		</div>
	</div>
</div>