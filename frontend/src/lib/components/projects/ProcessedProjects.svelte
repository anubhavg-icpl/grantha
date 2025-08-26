<script lang="ts">
	import { onMount } from 'svelte';
	import LoadingSpinner from '$lib/components/ui/LoadingSpinner.svelte';
	import Button from '$lib/components/ui/button.svelte';
	import Card from '$lib/components/ui/card.svelte';
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
		let filtered = projects.filter(project => 
			project.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
			project.owner.toLowerCase().includes(searchQuery.toLowerCase()) ||
			project.repo.toLowerCase().includes(searchQuery.toLowerCase()) ||
			project.repo_type.toLowerCase().includes(searchQuery.toLowerCase())
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
			const response = await fetch('http://localhost:8000/api/processed_projects');
			if (!response.ok) {
				throw new Error(`Failed to fetch projects: ${response.statusText}`);
			}
			
			const data = await response.json();
			if (data.error) {
				throw new Error(data.error);
			}
			
			projects = Array.isArray(data) ? data : [];
		} catch (e) {
			console.error('Failed to load projects from API:', e);
			error = e instanceof Error ? e.message : 'An unknown error occurred.';
			projects = [];
		} finally {
			isLoading = false;
		}
	}
	
	function clearSearch() {
		searchQuery = '';
	}
	
	async function handleDelete(project: ProcessedProjectEntry) {
		if (!confirm(`Are you sure you want to delete project ${project.name}?`)) {
			return;
		}
		
		try {
			const params = new URLSearchParams({
				owner: project.owner,
				repo: project.repo,
				repo_type: project.repo_type,
				language: project.language
			});
			
			const response = await fetch(`http://localhost:8000/api/wiki_cache?${params}`, {
				method: 'DELETE',
				headers: { 'Content-Type': 'application/json' }
			});
			
			if (!response.ok) {
				const errorBody = await response.json().catch(() => ({ error: response.statusText }));
				throw new Error(errorBody.error || response.statusText);
			}
			
			projects = projects.filter(p => p.id !== project.id);
		} catch (e) {
			console.error('Failed to delete project:', e);
			alert(`Failed to delete project: ${e instanceof Error ? e.message : 'Unknown error'}`);
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
				Search projects by name, owner, or repository
			</label>
			<input
				id="project-search"
				type="text"
				bind:value={searchQuery}
				placeholder="Search projects by name, owner, or repository..."
				aria-label="Search projects by name, owner, or repository"
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
			<Button onclick={fetchProjects}>Try Again</Button>
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
			<p class="text-japanese-muted mb-4">
				No projects found in the server cache. The cache might be empty or the server encountered an issue.
			</p>
			<Button onclick={() => window.location.href = '/wiki'} aria-label="Navigate to wiki generation page">Generate Wiki</Button>
		</div>
	{/if}
</div>