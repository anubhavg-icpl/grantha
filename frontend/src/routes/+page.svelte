<script lang="ts">
	import { onMount } from 'svelte';
	import { modelsState, modelsActions } from '$stores/models';
	import { chatState } from '$stores/chat';
	import { 
		MessageSquare, 
		BookOpen, 
		Search, 
		Brain, 
		Users,
		TrendingUp,
		Clock,
		Zap,
		ArrowRight,
		Sparkles,
		Shield,
		Globe,
		Cpu,
		Database,
		FileText,
		FolderOpen
	} from 'lucide-svelte';
	import Button from '$lib/components/ui/button.svelte';
	import LoadingSpinner from '$lib/components/ui/LoadingSpinner.svelte';
	import Card from '$lib/components/ui/card.svelte';
	import Badge from '$lib/components/ui/badge.svelte';
	import ProcessedProjects from '$lib/components/projects/ProcessedProjects.svelte';
	import type { ProcessedProjectEntry } from '$lib/types/api';

	interface DashboardCard {
		title: string;
		href: string;
		icon: any;
		description: string;
		color: string;
	}

	const cards: DashboardCard[] = [
		{
			title: 'Chat',
			href: '/chat',
			icon: MessageSquare,
			description: 'Start conversations with AI models',
			color: 'bg-blue-500'
		},
		{
			title: 'Wiki',
			href: '/wiki',
			icon: BookOpen,
			description: 'Generate and browse documentation',
			color: 'bg-green-500'
		},
		{
			title: 'Projects',
			href: '/projects',
			icon: FolderOpen,
			description: 'Manage your generated wikis and projects',
			color: 'bg-indigo-500'
		},
		{
			title: 'Research',
			href: '/research',
			icon: Search,
			description: 'Deep research and analysis tools',
			color: 'bg-purple-500'
		},
		{
			title: 'Models',
			href: '/models',
			icon: Brain,
			description: 'Configure AI models and providers',
			color: 'bg-orange-500'
		},
		{
			title: 'Agents',
			href: '/agents',
			icon: Users,
			description: 'Coordinate specialized AI agents',
			color: 'bg-pink-500'
		},
		{
			title: 'Simple',
			href: '/simple',
			icon: Zap,
			description: 'Quick AI interactions and RAG',
			color: 'bg-yellow-500'
		}
	];

	let stats = $state({
		totalChats: 0,
		activeModels: 0,
		totalProjects: 0,
		lastActivity: null as string | null
	});
	
	let recentProjects = $state<ProcessedProjectEntry[]>([]);

	onMount(async () => {
		// Calculate stats
		stats.totalChats = $chatState.conversations.length;
		stats.activeModels = $modelsState.config?.providers.length || 0;
		
		// Get last activity from most recent chat
		const lastChat = $chatState.conversations[0];
		if (lastChat) {
			stats.lastActivity = new Date(lastChat.updatedAt).toLocaleString();
		}
		
		// Load recent projects
		try {
			const response = await fetch('http://localhost:8000/api/processed_projects');
			if (response.ok) {
				const projects = await response.json();
				recentProjects = projects.slice(0, 3); // Show only 3 most recent
				stats.totalProjects = projects.length;
			}
		} catch (error) {
			console.error('Failed to load recent projects:', error);
		}
	});
</script>

<svelte:head>
	<title>Dashboard - Grantha</title>
</svelte:head>

<div class="space-y-12 paper-texture min-h-screen">
	<!-- Hero Section -->
	<div class="relative">
		<!-- Background gradient with Japanese aesthetic -->
		<div class="absolute inset-0 bg-gradient-to-br from-japanese-primary/5 to-japanese-secondary/10 rounded-3xl"></div>
		<div class="relative text-center py-16 px-8">
			<div class="flex items-center justify-center mb-6">
				<Badge variant="secondary" class="px-4 py-2">
					<Sparkles class="w-4 h-4 mr-2" />
					AI-Powered Platform
				</Badge>
			</div>
			<h1 class="text-5xl font-bold text-foreground mb-6 font-serif">
				Welcome to <span class="text-japanese-primary">Grantha</span>
			</h1>
			<p class="text-xl text-japanese-muted max-w-3xl mx-auto mb-8 leading-relaxed">
				Your comprehensive AI platform for intelligent documentation, interactive chat, 
				deep research, and sophisticated agent coordination. Experience the harmony of 
				cutting-edge technology with thoughtful design.
			</p>
			<div class="flex flex-col sm:flex-row gap-4 justify-center">
				<Button size="lg" class="text-lg px-8" onclick={() => window.location.href='/chat'}>
					<MessageSquare class="mr-2 h-5 w-5" />
					Start Chatting
					<ArrowRight class="ml-2 h-5 w-5" />
				</Button>
				<Button variant="outline" size="lg" class="text-lg px-8" onclick={() => window.location.href='/docs'}>
					<FileText class="mr-2 h-5 w-5" />
					View Documentation
				</Button>
			</div>
		</div>
	</div>

	<!-- Stats Overview -->
	<div class="grid grid-cols-1 md:grid-cols-4 gap-6">
		<Card class="p-6">
			<div class="flex items-center justify-between">
				<div>
					<p class="text-sm font-medium text-muted-foreground">Total Conversations</p>
					<p class="text-3xl font-bold text-foreground">{stats.totalChats}</p>
				</div>
				<div class="p-3 rounded-full bg-blue-500/10">
					<MessageSquare class="h-6 w-6 text-blue-500" />
				</div>
			</div>
		</Card>
		
		<Card class="p-6">
			<div class="flex items-center justify-between">
				<div>
					<p class="text-sm font-medium text-muted-foreground">Generated Projects</p>
					<p class="text-3xl font-bold text-foreground">{stats.totalProjects}</p>
				</div>
				<div class="p-3 rounded-full bg-indigo-500/10">
					<FolderOpen class="h-6 w-6 text-indigo-500" />
				</div>
			</div>
		</Card>
		
		<Card class="p-6">
			<div class="flex items-center justify-between">
				<div>
					<p class="text-sm font-medium text-muted-foreground">Available Providers</p>
					<p class="text-3xl font-bold text-foreground">{stats.activeModels}</p>
				</div>
				<div class="p-3 rounded-full bg-purple-500/10">
					<Brain class="h-6 w-6 text-purple-500" />
				</div>
			</div>
		</Card>
		
		<Card class="p-6">
			<div class="flex items-center justify-between">
				<div>
					<p class="text-sm font-medium text-muted-foreground">Last Activity</p>
					<p class="text-sm text-foreground">
						{stats.lastActivity || 'No activity yet'}
					</p>
				</div>
				<div class="p-3 rounded-full bg-green-500/10">
					<Clock class="h-6 w-6 text-green-500" />
				</div>
			</div>
		</Card>
	</div>

	<!-- Recent Projects Section -->
	{#if recentProjects.length > 0}
		<div>
			<div class="flex items-center justify-between mb-6">
				<h2 class="text-2xl font-bold text-foreground font-serif">Recent Projects</h2>
				<a href="/projects" class="text-japanese-link hover:underline flex items-center">
					View All
					<ArrowRight class="ml-1 h-4 w-4" />
				</a>
			</div>
			<div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
				{#each recentProjects as project}
					<Card class="p-4 hover:shadow-lg transition-shadow">
						<a href="/wiki?owner={project.owner}&repo={project.repo}&type={project.repo_type}&language={project.language}" class="block">
							<h3 class="text-lg font-semibold text-japanese-link hover:underline mb-2 truncate">
								{project.name}
							</h3>
							<div class="flex flex-wrap gap-2 mb-2">
								<Badge variant="secondary" class="text-xs">
									{project.repo_type}
								</Badge>
								<Badge variant="outline" class="text-xs">
									{project.language}
								</Badge>
							</div>
							<p class="text-xs text-muted-foreground">
								Processed: {new Date(project.submittedAt).toLocaleDateString()}
							</p>
						</a>
					</Card>
				{/each}
			</div>
		</div>
	{/if}

	<!-- Feature Cards -->
	<div>
		<div class="text-center mb-10">
			<h2 class="text-3xl font-bold text-foreground mb-4">Powerful Features</h2>
			<p class="text-muted-foreground max-w-2xl mx-auto">
				Discover all the ways Grantha can enhance your AI workflow and boost productivity.
			</p>
		</div>
		<div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
			{#each cards as card}
				{@const IconComponent = card.icon}
				<a
					href={card.href}
					class="group block"
				>
					<div class="card-japanese p-6 h-full shadow-custom border-2 border-transparent hover:border-japanese-primary/20 group-hover:scale-[1.02]">
						<div class="flex items-center mb-4">
							<div class="p-3 rounded-xl {card.color} text-white mr-4 shadow-custom">
								<IconComponent class="h-6 w-6" />
							</div>
							<div>
								<h3 class="text-lg font-semibold text-foreground group-hover:text-japanese-primary transition-colors font-serif">
									{card.title}
								</h3>
							</div>
						</div>
						<p class="text-japanese-muted text-sm mb-4 leading-relaxed">
							{card.description}
						</p>
						<div class="flex items-center text-sm text-japanese-link group-hover:translate-x-1 transition-transform">
							Learn more
							<ArrowRight class="ml-1 h-4 w-4" />
						</div>
					</div>
				</a>
			{/each}
		</div>
	</div>

	<!-- Platform Highlights -->
	<div class="grid grid-cols-1 lg:grid-cols-2 gap-8">
		<div class="card-japanese p-8 bg-gradient-to-br from-japanese-primary/5 to-japanese-secondary/10 border-japanese-primary/20">
			<div class="flex items-center mb-4">
				<div class="p-3 rounded-full bg-japanese-primary shadow-custom">
					<Cpu class="h-6 w-6 text-white" />
				</div>
				<div class="ml-4">
					<h3 class="text-xl font-semibold text-japanese-primary font-serif">Multi-Provider AI</h3>
					<p class="text-japanese-muted">Support for multiple AI providers and models</p>
				</div>
			</div>
			<ul class="space-y-2 text-sm text-japanese-muted">
				<li class="flex items-center">
					<div class="w-2 h-2 bg-japanese-primary rounded-full mr-2"></div>
					OpenAI, Claude, Llama, and more
				</li>
				<li class="flex items-center">
					<div class="w-2 h-2 bg-japanese-primary rounded-full mr-2"></div>
					Custom model endpoints
				</li>
				<li class="flex items-center">
					<div class="w-2 h-2 bg-japanese-primary rounded-full mr-2"></div>
					Dynamic model switching
				</li>
			</ul>
		</div>

		<div class="card-japanese p-8 bg-gradient-to-br from-japanese-highlight/5 to-japanese-secondary/10 border-japanese-highlight/20">
			<div class="flex items-center mb-4">
				<div class="p-3 rounded-full bg-japanese-highlight shadow-custom">
					<Shield class="h-6 w-6 text-white" />
				</div>
				<div class="ml-4">
					<h3 class="text-xl font-semibold text-japanese-highlight font-serif">Enterprise Ready</h3>
					<p class="text-japanese-muted">Built for security and scalability</p>
				</div>
			</div>
			<ul class="space-y-2 text-sm text-japanese-muted">
				<li class="flex items-center">
					<div class="w-2 h-2 bg-japanese-highlight rounded-full mr-2"></div>
					End-to-end encryption
				</li>
				<li class="flex items-center">
					<div class="w-2 h-2 bg-japanese-highlight rounded-full mr-2"></div>
					Role-based access control
				</li>
				<li class="flex items-center">
					<div class="w-2 h-2 bg-japanese-highlight rounded-full mr-2"></div>
					Audit logging & compliance
				</li>
			</ul>
		</div>
	</div>

	<!-- Quick Actions -->
	<div class="card-japanese p-8 shadow-custom">
		<div class="text-center mb-6">
			<h3 class="text-xl font-semibold text-foreground mb-2 font-serif">Quick Actions</h3>
			<p class="text-japanese-muted">Jump into any feature to get started immediately</p>
		</div>
		<div class="flex flex-wrap justify-center gap-3">
			<button class="btn-japanese flex items-center text-lg px-6 py-3" onclick={() => window.location.href='/chat'}>
				<MessageSquare class="mr-2 h-5 w-5" />
				New Chat
			</button>
			<button class="bg-transparent border border-japanese-border text-japanese-muted hover:bg-japanese-primary/10 hover:text-japanese-primary hover:border-japanese-primary px-6 py-3 rounded transition-all duration-300 flex items-center text-lg" onclick={() => window.location.href='/wiki'}>
				<BookOpen class="mr-2 h-5 w-5" />
				Generate Wiki
			</button>
			<button class="bg-transparent border border-japanese-border text-japanese-muted hover:bg-japanese-primary/10 hover:text-japanese-primary hover:border-japanese-primary px-6 py-3 rounded transition-all duration-300 flex items-center text-lg" onclick={() => window.location.href='/projects'}>
				<FolderOpen class="mr-2 h-5 w-5" />
				View Projects
			</button>
			<button class="bg-transparent border border-japanese-border text-japanese-muted hover:bg-japanese-primary/10 hover:text-japanese-primary hover:border-japanese-primary px-6 py-3 rounded transition-all duration-300 flex items-center text-lg" onclick={() => window.location.href='/research'}>
				<Search class="mr-2 h-5 w-5" />
				Start Research
			</button>
			<button class="bg-transparent border border-japanese-border text-japanese-muted hover:bg-japanese-primary/10 hover:text-japanese-primary hover:border-japanese-primary px-6 py-3 rounded transition-all duration-300 flex items-center text-lg" onclick={() => window.location.href='/models'}>
				<Brain class="mr-2 h-5 w-5" />
				Configure Models
			</button>
		</div>
	</div>

	<!-- Status -->
	{#if $modelsState.isLoading}
		<div class="flex justify-center py-8">
			<LoadingSpinner text="Loading configuration..." />
		</div>
	{:else if $modelsState.error}
		<div class="rounded-lg border border-destructive/20 bg-destructive/10 p-4">
			<p class="text-sm text-destructive">
				Error loading configuration: {$modelsState.error}
			</p>
			<Button 
				variant="outline" 
				size="sm" 
				class="mt-2"
				onclick={modelsActions.refresh}
			>
				Retry
			</Button>
		</div>
	{/if}
</div>