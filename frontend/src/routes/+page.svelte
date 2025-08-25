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
		FileText
	} from 'lucide-svelte';
	import Button from '$lib/components/ui/button.svelte';
	import LoadingSpinner from '$lib/components/ui/LoadingSpinner.svelte';
	import Card from '$lib/components/ui/card.svelte';
	import Badge from '$lib/components/ui/badge.svelte';

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
		lastActivity: null as string | null
	});

	onMount(() => {
		// Calculate stats
		stats.totalChats = $chatState.conversations.length;
		stats.activeModels = $modelsState.config?.providers.length || 0;
		
		// Get last activity from most recent chat
		const lastChat = $chatState.conversations[0];
		if (lastChat) {
			stats.lastActivity = new Date(lastChat.updatedAt).toLocaleString();
		}
	});
</script>

<svelte:head>
	<title>Dashboard - Grantha</title>
</svelte:head>

<div class="space-y-12">
	<!-- Hero Section -->
	<div class="relative">
		<!-- Background gradient -->
		<div class="absolute inset-0 gradient-bg rounded-3xl"></div>
		<div class="relative text-center py-16 px-8">
			<div class="flex items-center justify-center mb-6">
				<Badge variant="secondary" class="px-4 py-2">
					<Sparkles class="w-4 h-4 mr-2" />
					AI-Powered Platform
				</Badge>
			</div>
			<h1 class="text-5xl font-bold text-foreground mb-6">
				Welcome to <span class="text-primary">Grantha</span>
			</h1>
			<p class="text-xl text-muted-foreground max-w-3xl mx-auto mb-8">
				Your comprehensive AI platform for intelligent documentation, interactive chat, 
				deep research, and sophisticated agent coordination. Streamline your workflow with 
				cutting-edge AI technology.
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
	<div class="grid grid-cols-1 md:grid-cols-3 gap-6">
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
					<Card class="p-6 h-full transition-all hover:shadow-lg hover:scale-[1.02] border-2 border-transparent hover:border-primary/20">
						<div class="flex items-center mb-4">
							<div class="p-3 rounded-xl {card.color} text-white mr-4">
								<IconComponent class="h-6 w-6" />
							</div>
							<div>
								<h3 class="text-lg font-semibold text-foreground group-hover:text-primary transition-colors">
									{card.title}
								</h3>
							</div>
						</div>
						<p class="text-muted-foreground text-sm mb-4">
							{card.description}
						</p>
						<div class="flex items-center text-sm text-primary group-hover:translate-x-1 transition-transform">
							Learn more
							<ArrowRight class="ml-1 h-4 w-4" />
						</div>
					</Card>
				</a>
			{/each}
		</div>
	</div>

	<!-- Platform Highlights -->
	<div class="grid grid-cols-1 lg:grid-cols-2 gap-8">
		<Card class="p-8 bg-gradient-to-br from-blue-50 to-indigo-50 dark:from-blue-950/20 dark:to-indigo-950/20 border-blue-200 dark:border-blue-800">
			<div class="flex items-center mb-4">
				<div class="p-3 rounded-full bg-blue-500">
					<Cpu class="h-6 w-6 text-white" />
				</div>
				<div class="ml-4">
					<h3 class="text-xl font-semibold text-blue-900 dark:text-blue-100">Multi-Provider AI</h3>
					<p class="text-blue-600 dark:text-blue-300">Support for multiple AI providers and models</p>
				</div>
			</div>
			<ul class="space-y-2 text-sm text-blue-800 dark:text-blue-200">
				<li class="flex items-center">
					<div class="w-2 h-2 bg-blue-400 rounded-full mr-2"></div>
					OpenAI, Claude, Llama, and more
				</li>
				<li class="flex items-center">
					<div class="w-2 h-2 bg-blue-400 rounded-full mr-2"></div>
					Custom model endpoints
				</li>
				<li class="flex items-center">
					<div class="w-2 h-2 bg-blue-400 rounded-full mr-2"></div>
					Dynamic model switching
				</li>
			</ul>
		</Card>

		<Card class="p-8 bg-gradient-to-br from-green-50 to-emerald-50 dark:from-green-950/20 dark:to-emerald-950/20 border-green-200 dark:border-green-800">
			<div class="flex items-center mb-4">
				<div class="p-3 rounded-full bg-green-500">
					<Shield class="h-6 w-6 text-white" />
				</div>
				<div class="ml-4">
					<h3 class="text-xl font-semibold text-green-900 dark:text-green-100">Enterprise Ready</h3>
					<p class="text-green-600 dark:text-green-300">Built for security and scalability</p>
				</div>
			</div>
			<ul class="space-y-2 text-sm text-green-800 dark:text-green-200">
				<li class="flex items-center">
					<div class="w-2 h-2 bg-green-400 rounded-full mr-2"></div>
					End-to-end encryption
				</li>
				<li class="flex items-center">
					<div class="w-2 h-2 bg-green-400 rounded-full mr-2"></div>
					Role-based access control
				</li>
				<li class="flex items-center">
					<div class="w-2 h-2 bg-green-400 rounded-full mr-2"></div>
					Audit logging & compliance
				</li>
			</ul>
		</Card>
	</div>

	<!-- Quick Actions -->
	<Card class="p-6">
		<div class="text-center mb-6">
			<h3 class="text-xl font-semibold text-foreground mb-2">Quick Actions</h3>
			<p class="text-muted-foreground">Jump into any feature to get started immediately</p>
		</div>
		<div class="flex flex-wrap justify-center gap-3">
			<Button size="lg" class="flex items-center" onclick={() => window.location.href='/chat'}>
				<MessageSquare class="mr-2 h-5 w-5" />
				New Chat
			</Button>
			<Button variant="outline" size="lg" class="flex items-center" onclick={() => window.location.href='/wiki'}>
				<BookOpen class="mr-2 h-5 w-5" />
				Generate Wiki
			</Button>
			<Button variant="outline" size="lg" class="flex items-center" onclick={() => window.location.href='/research'}>
				<Search class="mr-2 h-5 w-5" />
				Start Research
			</Button>
			<Button variant="outline" size="lg" class="flex items-center" onclick={() => window.location.href='/models'}>
				<Brain class="mr-2 h-5 w-5" />
				Configure Models
			</Button>
		</div>
	</Card>

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