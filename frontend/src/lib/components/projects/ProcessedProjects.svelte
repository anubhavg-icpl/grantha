<script lang="ts">
	import { onMount } from 'svelte';
	import LoadingSpinner from '$lib/components/ui/LoadingSpinner.svelte';
	import Button from '$lib/components/ui/button.svelte';
	import Card from '$lib/components/ui/card.svelte';
	import { apiClient } from '$lib/api/client';
	import type { ProcessedProjectEntry } from '$lib/types/api';
	
	interface Props {
		showHeader?: boolean;
		maxItems?: number;
		className?: string;
	}
	
	let { 
		showHeader = true, 
		maxItems,
		className = ''
	}: Props = $props();
	
	let projects: ProcessedProjectEntry[] = $state([]);
	let isLoading = $state(true);
	let error: string | null = $state(null);
	let searchQuery = $state('');
	let viewMode: 'card' | 'list' = $state('card');
	
	// Filter and limit projects
	let filteredProjects = $derived.by(() => {
		if (!searchQuery.trim()) {
			return maxItems ? projects.slice(0, maxItems) : projects;
		}
		
		const query = searchQuery.toLowerCase().trim();
		let filtered = projects.filter(project => 
			project.name.toLowerCase().includes(query) ||
			project.owner.toLowerCase().includes(query) ||
			project.repo.toLowerCase().includes(query) ||
			project.repo_type.toLowerCase().includes(query) ||
			project.language.toLowerCase().includes(query) ||
			(project.provider && project.provider.toLowerCase().includes(query)) ||
			(project.model && project.model.toLowerCase().includes(query))
		);
		
		return maxItems ? filtered.slice(0, maxItems) : filtered;
	});
	
	onMount(async () => {
		await fetchProjects();
	});
	
	async function fetchProjects() {
		isLoading = true;
		error = null;
		
		try {
			// Try the new wiki/projects endpoint first, fallback to legacy endpoint
			try {
				projects = await apiClient.getWikiProjects();
				console.log(`Successfully loaded ${projects.length} projects from wiki/projects endpoint`);
			} catch (wikiError) {
				console.warn('Wiki projects endpoint failed, trying legacy endpoint:', wikiError);
				projects = await apiClient.getProcessedProjects();
				console.log(`Successfully loaded ${projects.length} projects from legacy endpoint`);
			}
			
			if (!Array.isArray(projects)) {
				throw new Error('Invalid response format: Expected an array of projects');
			}
		} catch (e) {
			console.error('Failed to load projects from API:', e);
			error = e instanceof Error ? e.message : 'An unknown error occurred while loading projects.';
			projects = [];
		} finally {
			isLoading = false;
		}
	}
	
	function clearSearch() {
		searchQuery = '';
	}
	
	async function handleDelete(project: ProcessedProjectEntry) {
		const confirmMessage = `Are you sure you want to delete project "${project.name}"?\n\nThis will remove:\n- All generated wiki pages\n- Project cache data\n- Processing history\n\nThis action cannot be undone.`;
		
		if (!confirm(confirmMessage)) {
			return;
		}
		
		try {
			console.log(`Deleting project: ${project.name} (${project.owner}/${project.repo})`);
			
			// Use the API client method instead of direct fetch
			await apiClient.deleteProjectCache(
				project.owner,
				project.repo,
				project.repo_type,
				project.language
			);
			
			// Remove from local state
			projects = projects.filter(p => p.id !== project.id);
			console.log(`Successfully deleted project: ${project.name}`);
			
			// Show success message
			alert(`Project "${project.name}" has been successfully deleted.`);
			
		} catch (e) {
			console.error('Failed to delete project:', e);
			const errorMessage = e instanceof Error ? e.message : 'Unknown error occurred';
			alert(`Failed to delete project "${project.name}":\n\n${errorMessage}\n\nPlease try again or contact support if the problem persists.`);
		}
	}
	
	function formatDate(timestamp: number): string {
		return new Date(timestamp).toLocaleDateString('en-US', {
			year: 'numeric',
			month: 'short',
			day: 'numeric'
		});
	}
	
	function getProjectUrl(project: ProcessedProjectEntry): string {
		return `/wiki?owner=${project.owner}&repo=${project.repo}&type=${project.repo_type}&language=${project.language}`;
	}
</script>

<div class={className}>
	{#if showHeader}
		<header class="mb-6">
			<div class="flex items-center justify-between">
				<h1 class="text-3xl font-bold text-japanese-primary">Processed Wiki Projects</h1>
				<a href="/" class="text-japanese-primary hover:underline">
					Back to Home
				</a>
			</div>
		</header>
	{/if}

	<!-- Search Bar and View Toggle -->
	<div class="mb-6 flex flex-col sm:flex-row gap-4">
		<!-- Search Bar -->
		<div class="relative flex-1">
			<label for="project-search" class="sr-only">
				Search projects by name, owner, repository, provider, or model
			</label>
			<input
				id="project-search"
				type="text"
				bind:value={searchQuery}
				placeholder="Search projects by name, owner, repository, provider, or model..."
				aria-label="Search projects by name, owner, repository, provider, or model"
				class="block w-full pl-4 pr-12 py-2.5 border border-japanese-border rounded-lg bg-japanese-card text-japanese-foreground placeholder:text-japanese-muted focus:outline-none focus:border-japanese-primary focus:ring-1 focus:ring-japanese-primary"
			/>
			{#if searchQuery}
				<button
					onclick={clearSearch}
					class="absolute inset-y-0 right-0 flex items-center pr-3 text-japanese-muted hover:text-japanese-foreground transition-colors"
					aria-label="Clear search"
				>
					<svg class="h-4 w-4" fill="currentColor" viewBox="0 0 20 20">
						<path fill-rule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clip-rule="evenodd"/>
					</svg>
				</button>
			{/if}
		</div>

		<!-- View Toggle -->
		<div class="flex items-center bg-japanese-card border border-japanese-border rounded-lg p-1">
			<button
				onclick={() => viewMode = 'card'}
				class="p-2 rounded transition-colors {viewMode === 'card' 
					? 'bg-japanese-primary text-white' 
					: 'text-japanese-muted hover:text-japanese-foreground hover:bg-japanese-card'}"
				title="Card View"
				aria-label="Card View"
			>
				<svg class="h-4 w-4" fill="currentColor" viewBox="0 0 20 20">
					<path d="M5 3a2 2 0 00-2 2v2a2 2 0 002 2h2a2 2 0 002-2V5a2 2 0 00-2-2H5zM5 11a2 2 0 00-2 2v2a2 2 0 002 2h2a2 2 0 002-2v-2a2 2 0 00-2-2H5zM11 5a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2V5zM11 13a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2v-2z"/>
				</svg>
			</button>
			<button
				onclick={() => viewMode = 'list'}
				class="p-2 rounded transition-colors {viewMode === 'list' 
					? 'bg-japanese-primary text-white' 
					: 'text-japanese-muted hover:text-japanese-foreground hover:bg-japanese-card'}"
				title="List View"
				aria-label="List View"
			>
				<svg class="h-4 w-4" fill="currentColor" viewBox="0 0 20 20">
					<path fill-rule="evenodd" d="M3 4a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1zm0 4a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1zm0 4a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1z" clip-rule="evenodd"/>
				</svg>
			</button>
		</div>
	</div>

	{#if isLoading}
		<div class="flex items-center justify-center py-8">
			<LoadingSpinner />
			<span class="ml-2 text-japanese-muted">Loading projects...</span>
		</div>
	{/if}

	{#if error}
		<div class="text-center py-8">
			<p class="text-japanese-highlight mb-4">Error loading projects: {error}</p>
			<Button onclick={fetchProjects}>
				{#snippet children()}Try Again{/snippet}
			</Button>
		</div>
	{/if}

	{#if !isLoading && !error && filteredProjects.length > 0}
		<div class="{viewMode === 'card' ? 'grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4' : 'space-y-2'}">
			{#each filteredProjects as project (project.id)}
				{#if viewMode === 'card'}
					<div class="relative p-4 border border-japanese-border rounded-lg bg-japanese-card shadow-sm hover:shadow-md transition-all duration-200 hover:scale-[1.02]">
						<button
							type="button"
							onclick={() => handleDelete(project)}
							class="absolute top-2 right-2 text-japanese-muted hover:text-japanese-foreground"
							title="Delete project"
							aria-label="Delete project {project.name}"
						>
							<svg class="h-4 w-4" fill="currentColor" viewBox="0 0 20 20">
								<path fill-rule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clip-rule="evenodd"/>
							</svg>
						</button>
						<a href={getProjectUrl(project)} class="block">
							<h3 class="text-lg font-semibold text-japanese-link hover:underline mb-2 line-clamp-2">
								{project.name}
							</h3>
							<div class="flex flex-wrap gap-2 mb-3">
								<span class="px-2 py-1 text-xs bg-japanese-primary/10 text-japanese-primary rounded-full border border-japanese-primary/20">
									{project.repo_type}
								</span>
								<span class="px-2 py-1 text-xs bg-japanese-background text-japanese-muted rounded-full border border-japanese-border">
									{project.language}
								</span>
								{#if project.provider}
									<span class="px-2 py-1 text-xs bg-green-100 text-green-800 rounded-full border border-green-200">
										{project.provider}
									</span>
								{/if}
								{#if project.model}
									<span class="px-2 py-1 text-xs bg-blue-100 text-blue-800 rounded-full border border-blue-200">
										{project.model}
									</span>
								{/if}
							</div>
							<p class="text-xs text-japanese-muted">
								Processed on: {formatDate(project.submittedAt)}
							</p>
						</a>
					</div>
				{:else}
					<div class="relative p-3 border border-japanese-border rounded-lg bg-japanese-card hover:bg-japanese-background transition-colors">
						<button
							type="button"
							onclick={() => handleDelete(project)}
							class="absolute top-2 right-2 text-japanese-muted hover:text-japanese-foreground"
							title="Delete project"
							aria-label="Delete project {project.name}"
						>
							<svg class="h-4 w-4" fill="currentColor" viewBox="0 0 20 20">
								<path fill-rule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clip-rule="evenodd"/>
							</svg>
						</button>
						<a href={getProjectUrl(project)} class="flex items-center justify-between">
							<div class="flex-1 min-w-0">
								<h3 class="text-base font-medium text-japanese-link hover:underline truncate">
									{project.name}
								</h3>
								<p class="text-xs text-japanese-muted mt-1">
									Processed on: {formatDate(project.submittedAt)} • {project.repo_type} • {project.language}
									{#if project.provider}• {project.provider}{/if}
									{#if project.model}• {project.model}{/if}
								</p>
							</div>
							<div class="flex gap-2 ml-4">
								<span class="px-2 py-1 text-xs bg-japanese-primary/10 text-japanese-primary rounded border border-japanese-primary/20">
									{project.repo_type}
								</span>
							</div>
						</a>
					</div>
				{/if}
			{/each}
		</div>
	{/if}

	{#if !isLoading && !error && projects.length > 0 && filteredProjects.length === 0 && searchQuery}
		<p class="text-japanese-muted text-center py-8">No projects match your search criteria.</p>
	{/if}

	{#if !isLoading && !error && projects.length === 0}
		<div class="text-center py-12">
			<svg class="w-16 h-16 mx-auto mb-4 text-japanese-muted/50" fill="currentColor" viewBox="0 0 20 20">
				<path d="M4 3a2 2 0 100 4h12a2 2 0 100-4H4z"/>
				<path fill-rule="evenodd" d="M3 8h14v7a2 2 0 01-2 2H5a2 2 0 01-2-2V8zm5 3a1 1 0 011-1h2a1 1 0 110 2H9a1 1 0 01-1-1z" clip-rule="evenodd"/>
			</svg>
			<h3 class="text-lg font-medium text-japanese-foreground mb-2">No Projects Found</h3>
			<p class="text-japanese-muted mb-6 max-w-md mx-auto">
				No processed projects found. Start by generating wiki documentation for your repositories to see them listed here.
			</p>
			<div class="flex gap-3 justify-center">
				<Button onclick={() => window.location.href = '/wiki'} aria-label="Navigate to wiki generation page">
					{#snippet children()}
						<svg class="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
							<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4"/>
						</svg>
						Generate Wiki
					{/snippet}
				</Button>
				<Button 
					variant="outline" 
					onclick={fetchProjects} 
					aria-label="Refresh projects list"
				>
					{#snippet children()}
						<svg class="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
							<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"/>
						</svg>
						Refresh
					{/snippet}
				</Button>
			</div>
		</div>
	{/if}
</div>