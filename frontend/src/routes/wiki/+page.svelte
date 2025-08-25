<script lang="ts">
	import { BookOpen, Plus, Search, FileText, ExternalLink } from 'lucide-svelte';
	import Button from '$lib/components/ui/button.svelte';
	import Input from '$lib/components/ui/input.svelte';

	let repoUrl = $state('');
	let searchQuery = $state('');
	let isGenerating = $state(false);

	function handleGenerateWiki() {
		if (!repoUrl.trim()) return;
		
		isGenerating = true;
		// TODO: Implement wiki generation
		setTimeout(() => {
			isGenerating = false;
		}, 2000);
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
					/>
				</div>
				
				<Button
					class="w-full"
					loading={isGenerating}
					disabled={!repoUrl.trim() || isGenerating}
					on:click={handleGenerateWiki}
				>
					<BookOpen class="mr-2 h-4 w-4" />
					Generate Wiki Documentation
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
					<Search class="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-muted-foreground" />
					<Input
						placeholder="Search wikis..."
						bind:value={searchQuery}
						class="pl-10 w-64"
					/>
				</div>
			</div>
		</div>

		<!-- Wiki Grid -->
		<div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
			<!-- Sample wiki cards -->
			<div class="rounded-lg border bg-card p-6 hover:shadow-md transition-shadow">
				<div class="flex items-start justify-between mb-3">
					<div class="flex items-center">
						<BookOpen class="h-5 w-5 text-primary mr-2" />
						<h3 class="font-semibold text-foreground">Sample Project</h3>
					</div>
					<Button size="icon" variant="ghost" class="h-8 w-8">
						<ExternalLink class="h-4 w-4" />
					</Button>
				</div>
				
				<p class="text-sm text-muted-foreground mb-4">
					A comprehensive wiki for a sample TypeScript project with API documentation and guides.
				</p>
				
				<div class="flex items-center justify-between text-xs text-muted-foreground">
					<span>Generated 2 hours ago</span>
					<span>15 pages</span>
				</div>
			</div>

			<div class="rounded-lg border bg-card p-6 hover:shadow-md transition-shadow">
				<div class="flex items-start justify-between mb-3">
					<div class="flex items-center">
						<BookOpen class="h-5 w-5 text-primary mr-2" />
						<h3 class="font-semibold text-foreground">React Components</h3>
					</div>
					<Button size="icon" variant="ghost" class="h-8 w-8">
						<ExternalLink class="h-4 w-4" />
					</Button>
				</div>
				
				<p class="text-sm text-muted-foreground mb-4">
					Documentation for a React component library with examples and usage guides.
				</p>
				
				<div class="flex items-center justify-between text-xs text-muted-foreground">
					<span>Generated 1 day ago</span>
					<span>23 pages</span>
				</div>
			</div>

			<div class="rounded-lg border bg-card p-6 hover:shadow-md transition-shadow">
				<div class="flex items-start justify-between mb-3">
					<div class="flex items-center">
						<BookOpen class="h-5 w-5 text-primary mr-2" />
						<h3 class="font-semibold text-foreground">API Backend</h3>
					</div>
					<Button size="icon" variant="ghost" class="h-8 w-8">
						<ExternalLink class="h-4 w-4" />
					</Button>
				</div>
				
				<p class="text-sm text-muted-foreground mb-4">
					Complete API documentation with endpoints, schemas, and integration examples.
				</p>
				
				<div class="flex items-center justify-between text-xs text-muted-foreground">
					<span>Generated 3 days ago</span>
					<span>31 pages</span>
				</div>
			</div>
		</div>

		<!-- Empty state when no results -->
		{#if searchQuery && searchQuery.length > 0}
			<div class="text-center py-12">
				<Search class="h-12 w-12 text-muted-foreground mx-auto mb-4" />
				<h3 class="text-lg font-semibold text-foreground mb-2">No wikis found</h3>
				<p class="text-muted-foreground">
					No wikis match your search query "{searchQuery}"
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