<script lang="ts">
	import { BookOpen, Plus, Search, FileText, ExternalLink, AlertCircle, CheckCircle, Eye, ChevronRight, X } from 'lucide-svelte';
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
	let previewWiki = $state<WikiStructureModel | null>(null);
	let showPreview = $state(false);

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

	function openPreview(wiki: WikiStructureModel) {
		previewWiki = wiki;
		showPreview = true;
	}

	function closePreview() {
		showPreview = false;
		setTimeout(() => {
			previewWiki = null;
		}, 300);
	}
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
						<div class="mt-3">
							<Button 
								variant="outline" 
								size="sm" 
								class="w-full"
								onclick={() => generationResult.wiki_structure && openPreview(generationResult.wiki_structure)}
							>
								<Eye class="mr-2 h-4 w-4" />
								Preview Wiki
							</Button>
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
							<div class="flex items-center flex-1 min-w-0">
								<BookOpen class="h-5 w-5 text-primary mr-2 flex-shrink-0" />
								<h3 class="font-semibold text-foreground truncate">{wiki.title}</h3>
							</div>
							<div class="flex items-center gap-1 ml-2">
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
						</div>
						
						<p class="text-sm text-muted-foreground mb-4 line-clamp-3">
							{wiki.description || 'No description available'}
						</p>
						
						<div class="flex items-center justify-between mb-3 text-xs text-muted-foreground">
							<span>
								{#if wiki.generated_at}
									Generated {new Date(wiki.generated_at).toLocaleDateString()}
								{:else}
									Recent
								{/if}
							</span>
							<span>{wiki.pages?.length || 0} pages</span>
						</div>
						
						<Button
							variant="outline"
							size="sm"
							class="w-full"
							onclick={() => openPreview(wiki)}
						>
							<Eye class="mr-2 h-4 w-4" />
							Preview Wiki
						</Button>
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

	<!-- Wiki Preview Modal -->
	{#if showPreview && previewWiki}
		<div 
			class="fixed inset-0 z-50 bg-background/80 backdrop-blur-sm"
			onclick={closePreview}
			role="button"
			tabindex="-1"
			aria-label="Close preview"
		>
			<div 
				class="fixed inset-x-4 top-4 bottom-4 md:inset-x-auto md:left-1/2 md:-translate-x-1/2 md:w-full md:max-w-5xl bg-background border rounded-lg shadow-lg overflow-hidden flex flex-col"
				onclick={(e) => e.stopPropagation()}
			>
				<!-- Header -->
				<div class="flex items-center justify-between p-6 border-b">
					<div class="flex items-center gap-3">
						<BookOpen class="h-6 w-6 text-primary" />
						<div>
							<h2 class="text-xl font-semibold text-foreground">{previewWiki.title}</h2>
							<p class="text-sm text-muted-foreground mt-1">{previewWiki.description}</p>
						</div>
					</div>
					<Button 
						size="icon" 
						variant="ghost"
						onclick={closePreview}
					>
						<X class="h-5 w-5" />
					</Button>
				</div>

				<!-- Content -->
				<div class="flex-1 overflow-y-auto p-6">
					{#if previewWiki.pages && previewWiki.pages.length > 0}
						<div class="space-y-8">
							{#each previewWiki.pages as page, index}
								<div class="prose prose-neutral dark:prose-invert max-w-none">
									<h2 class="text-2xl font-bold mb-4 flex items-center gap-2">
										<span class="text-primary">{index + 1}.</span>
										{page.title}
									</h2>
									
									{#if page.sections && page.sections.length > 0}
										<div class="space-y-6">
											{#each page.sections as section}
												<div>
													<h3 class="text-lg font-semibold mb-2 flex items-center gap-2">
														<ChevronRight class="h-4 w-4 text-muted-foreground" />
														{section.title}
													</h3>
													<div class="pl-6 space-y-3">
														{#if section.content}
															<p class="text-muted-foreground whitespace-pre-wrap">{section.content}</p>
														{/if}
														
														{#if section.code_examples && section.code_examples.length > 0}
															<div class="space-y-3">
																{#each section.code_examples as example}
																	<div class="bg-muted/50 rounded-lg p-4">
																		<div class="flex items-center justify-between mb-2">
																			<span class="text-xs font-medium text-muted-foreground">
																				{example.language || 'code'}
																			</span>
																			{#if example.file_path}
																				<span class="text-xs text-muted-foreground">
																					{example.file_path}
																				</span>
																			{/if}
																		</div>
																		<pre class="overflow-x-auto"><code class="text-sm">{example.code}</code></pre>
																		{#if example.explanation}
																			<p class="text-sm text-muted-foreground mt-2">{example.explanation}</p>
																		{/if}
																	</div>
																{/each}
															</div>
														{/if}
														
														{#if section.important_points && section.important_points.length > 0}
															<ul class="list-disc pl-5 space-y-1">
																{#each section.important_points as point}
																	<li class="text-sm text-muted-foreground">{point}</li>
																{/each}
															</ul>
														{/if}
													</div>
												</div>
											{/each}
										</div>
									{:else if page.content}
										<p class="text-muted-foreground whitespace-pre-wrap">{page.content}</p>
									{/if}
								</div>
							{/each}
						</div>
					{:else}
						<div class="text-center py-12">
							<FileText class="h-12 w-12 text-muted-foreground mx-auto mb-4" />
							<p class="text-muted-foreground">No pages available for preview</p>
						</div>
					{/if}
				</div>

				<!-- Footer -->
				<div class="flex items-center justify-between p-6 border-t">
					<div class="text-sm text-muted-foreground">
						{previewWiki?.pages?.length || 0} pages • Generated {previewWiki?.generated_at ? new Date(previewWiki.generated_at).toLocaleDateString() : 'recently'}
					</div>
					<div class="flex items-center gap-2">
						{#if previewWiki.repo_url}
							<Button 
								variant="outline"
								size="sm"
								onclick={() => window.open(previewWiki.repo_url, '_blank')}
							>
								<ExternalLink class="mr-2 h-4 w-4" />
								View Repository
							</Button>
						{/if}
						<Button 
							variant="default"
							size="sm"
							onclick={closePreview}
						>
							Close Preview
						</Button>
					</div>
				</div>
			</div>
		</div>
	{/if}
</div>