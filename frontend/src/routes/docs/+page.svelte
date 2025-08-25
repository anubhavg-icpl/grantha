<script lang="ts">
	import { onMount } from 'svelte';
	import { 
		FileText, 
		Book, 
		Code, 
		MessageSquare, 
		Search, 
		Settings, 
		ExternalLink,
		ChevronRight,
		Hash,
		Users,
		Brain
	} from 'lucide-svelte';
	import Button from '$lib/components/ui/button.svelte';
	import Input from '$lib/components/ui/input.svelte';
	import Card from '$lib/components/ui/card.svelte';
	import Badge from '$lib/components/ui/badge.svelte';

	interface DocSection {
		id: string;
		title: string;
		description: string;
		icon: any;
		items: DocItem[];
	}

	interface DocItem {
		id: string;
		title: string;
		description: string;
		href: string;
		isExternal?: boolean;
		badge?: string;
	}

	const docSections: DocSection[] = [
		{
			id: 'getting-started',
			title: 'Getting Started',
			description: 'Quick start guide and basic concepts',
			icon: Book,
			items: [
				{
					id: 'overview',
					title: 'Platform Overview',
					description: 'Learn about Grantha\'s core features and capabilities',
					href: '#overview'
				},
				{
					id: 'setup',
					title: 'Initial Setup',
					description: 'Configure your first AI model and start chatting',
					href: '#setup'
				},
				{
					id: 'first-chat',
					title: 'Your First Chat',
					description: 'Step-by-step guide to creating your first conversation',
					href: '#first-chat'
				},
				{
					id: 'navigation',
					title: 'Interface Navigation',
					description: 'Understanding the layout and navigation patterns',
					href: '#navigation'
				}
			]
		},
		{
			id: 'features',
			title: 'Core Features',
			description: 'Detailed guides for each platform feature',
			icon: MessageSquare,
			items: [
				{
					id: 'chat-interface',
					title: 'Chat Interface',
					description: 'Advanced chat features, streaming, and conversation management',
					href: '#chat-interface'
				},
				{
					id: 'wiki-generation',
					title: 'Wiki Generation',
					description: 'Automatically generate documentation from repositories',
					href: '#wiki-generation'
				},
				{
					id: 'research-tools',
					title: 'Research Tools',
					description: 'Deep research capabilities and source compilation',
					href: '#research-tools'
				},
				{
					id: 'simple-operations',
					title: 'Simple Operations',
					description: 'Quick chat and RAG operations for fast interactions',
					href: '#simple-operations'
				}
			]
		},
		{
			id: 'models',
			title: 'AI Models',
			description: 'Model configuration and management',
			icon: Brain,
			items: [
				{
					id: 'model-providers',
					title: 'Model Providers',
					description: 'Configure different AI providers and their models',
					href: '#model-providers'
				},
				{
					id: 'custom-models',
					title: 'Custom Models',
					description: 'Add and configure custom model endpoints',
					href: '#custom-models'
				},
				{
					id: 'model-settings',
					title: 'Model Settings',
					description: 'Temperature, tokens, and other model parameters',
					href: '#model-settings'
				}
			]
		},
		{
			id: 'agents',
			title: 'AI Agents',
			description: 'Multi-agent coordination and workflows',
			icon: Users,
			items: [
				{
					id: 'agent-overview',
					title: 'Agent System',
					description: 'Understanding the multi-agent architecture',
					href: '#agent-overview',
					badge: 'Advanced'
				},
				{
					id: 'agent-coordination',
					title: 'Agent Coordination',
					description: 'How agents work together to solve complex tasks',
					href: '#agent-coordination',
					badge: 'Advanced'
				},
				{
					id: 'agent-roles',
					title: 'Agent Roles',
					description: 'Different agent specializations and capabilities',
					href: '#agent-roles'
				}
			]
		},
		{
			id: 'api',
			title: 'API Reference',
			description: 'Technical documentation for developers',
			icon: Code,
			items: [
				{
					id: 'api-overview',
					title: 'API Overview',
					description: 'Introduction to the Grantha API endpoints',
					href: '#api-overview'
				},
				{
					id: 'authentication',
					title: 'Authentication',
					description: 'API authentication and security',
					href: '#authentication'
				},
				{
					id: 'endpoints',
					title: 'API Endpoints',
					description: 'Complete reference of all available endpoints',
					href: '#endpoints'
				},
				{
					id: 'websockets',
					title: 'WebSocket API',
					description: 'Real-time communication via WebSockets',
					href: '#websockets'
				}
			]
		},
		{
			id: 'troubleshooting',
			title: 'Help & Support',
			description: 'Common issues and troubleshooting',
			icon: Settings,
			items: [
				{
					id: 'common-issues',
					title: 'Common Issues',
					description: 'Solutions to frequently encountered problems',
					href: '#common-issues'
				},
				{
					id: 'error-codes',
					title: 'Error Codes',
					description: 'Understanding error messages and their solutions',
					href: '#error-codes'
				},
				{
					id: 'performance',
					title: 'Performance Tips',
					description: 'Optimize your Grantha experience',
					href: '#performance'
				},
				{
					id: 'support',
					title: 'Get Support',
					description: 'Contact information and community resources',
					href: 'https://github.com/grantha/support',
					isExternal: true
				}
			]
		}
	];

	let searchQuery = $state('');
	let filteredSections = $derived(
		searchQuery.trim()
			? docSections.map(section => ({
				...section,
				items: section.items.filter(item => 
					item.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
					item.description.toLowerCase().includes(searchQuery.toLowerCase())
				)
			})).filter(section => section.items.length > 0)
			: docSections
	);

	let selectedSection = $state<string | null>(null);

	const toggleSection = (sectionId: string) => {
		selectedSection = selectedSection === sectionId ? null : sectionId;
	};

	onMount(() => {
		// Handle hash navigation
		const hash = window.location.hash.slice(1);
		if (hash) {
			const element = document.getElementById(hash);
			if (element) {
				element.scrollIntoView({ behavior: 'smooth' });
			}
		}
	});
</script>

<svelte:head>
	<title>Documentation - Grantha</title>
</svelte:head>

<div class="space-y-6">
	<!-- Header -->
	<div class="text-center">
		<h1 class="text-3xl font-bold text-foreground mb-2">Documentation</h1>
		<p class="text-muted-foreground max-w-2xl mx-auto">
			Everything you need to know about using Grantha effectively. 
			From getting started to advanced features and API reference.
		</p>
	</div>

	<!-- Search -->
	<div class="max-w-md mx-auto">
		<div class="relative">
			<Search class="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-muted-foreground" />
			<Input
				placeholder="Search documentation..."
				bind:value={searchQuery}
				class="pl-10"
			/>
		</div>
	</div>

	<!-- Quick Links -->
	{#if !searchQuery.trim()}
		<div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
			<Card class="p-4 hover:shadow-md transition-shadow cursor-pointer">
				<div class="flex items-center mb-2">
					<Book class="h-5 w-5 text-primary mr-2" />
					<h3 class="font-medium">Quick Start</h3>
				</div>
				<p class="text-sm text-muted-foreground">Get up and running in minutes</p>
			</Card>

			<Card class="p-4 hover:shadow-md transition-shadow cursor-pointer">
				<div class="flex items-center mb-2">
					<MessageSquare class="h-5 w-5 text-primary mr-2" />
					<h3 class="font-medium">Chat Guide</h3>
				</div>
				<p class="text-sm text-muted-foreground">Master the chat interface</p>
			</Card>

			<Card class="p-4 hover:shadow-md transition-shadow cursor-pointer">
				<div class="flex items-center mb-2">
					<Code class="h-5 w-5 text-primary mr-2" />
					<h3 class="font-medium">API Reference</h3>
				</div>
				<p class="text-sm text-muted-foreground">Complete API documentation</p>
			</Card>

			<Card class="p-4 hover:shadow-md transition-shadow cursor-pointer">
				<div class="flex items-center mb-2">
					<Settings class="h-5 w-5 text-primary mr-2" />
					<h3 class="font-medium">Troubleshooting</h3>
				</div>
				<p class="text-sm text-muted-foreground">Common issues and solutions</p>
			</Card>
		</div>
	{/if}

	<!-- Documentation Sections -->
	<div class="space-y-6">
		{#each filteredSections as section}
			<Card class="overflow-hidden">
				<button
					type="button"
					class="w-full p-6 text-left hover:bg-muted/50 transition-colors"
					on:click={() => toggleSection(section.id)}
				>
					<div class="flex items-center justify-between">
						<div class="flex items-center space-x-3">
							<div class="p-2 rounded-lg bg-primary/10">
								<svelte:component this={section.icon} class="h-5 w-5 text-primary" />
							</div>
							<div>
								<h2 class="text-lg font-semibold text-foreground">{section.title}</h2>
								<p class="text-sm text-muted-foreground">{section.description}</p>
							</div>
						</div>
						<ChevronRight class="h-5 w-5 text-muted-foreground transition-transform {selectedSection === section.id ? 'rotate-90' : ''}" />
					</div>
				</button>

				{#if selectedSection === section.id || searchQuery.trim()}
					<div class="border-t bg-muted/20">
						<div class="p-6 space-y-4">
							{#each section.items as item}
								<div class="flex items-center justify-between p-3 rounded-lg border bg-background hover:bg-accent/50 transition-colors">
									<div class="flex-1">
										<div class="flex items-center space-x-2 mb-1">
											<a
												href={item.href}
												class="font-medium text-foreground hover:text-primary transition-colors"
												target={item.isExternal ? '_blank' : undefined}
												rel={item.isExternal ? 'noopener noreferrer' : undefined}
											>
												{item.title}
											</a>
											{#if item.badge}
												<Badge variant="secondary" class="text-xs">
													{item.badge}
												</Badge>
											{/if}
											{#if item.isExternal}
												<ExternalLink class="h-3 w-3 text-muted-foreground" />
											{/if}
										</div>
										<p class="text-sm text-muted-foreground">{item.description}</p>
									</div>
									<Hash class="h-4 w-4 text-muted-foreground ml-3" />
								</div>
							{/each}
						</div>
					</div>
				{/if}
			</Card>
		{/each}

		{#if filteredSections.length === 0}
			<div class="text-center py-12">
				<Search class="h-12 w-12 text-muted-foreground mx-auto mb-4" />
				<h3 class="text-lg font-semibold text-foreground mb-2">No results found</h3>
				<p class="text-muted-foreground">
					No documentation matches your search query "{searchQuery}"
				</p>
				<Button variant="outline" class="mt-4" on:click={() => searchQuery = ''}>
					Clear Search
				</Button>
			</div>
		{/if}
	</div>

	<!-- Footer -->
	{#if !searchQuery.trim()}
		<Card class="p-6">
			<div class="text-center">
				<h3 class="text-lg font-semibold text-foreground mb-2">Need more help?</h3>
				<p class="text-muted-foreground mb-4">
					Can't find what you're looking for? Check out our community resources or get in touch.
				</p>
				<div class="flex justify-center space-x-3">
					<Button variant="outline" size="sm">
						<ExternalLink class="mr-2 h-4 w-4" />
						GitHub Issues
					</Button>
					<Button variant="outline" size="sm">
						<MessageSquare class="mr-2 h-4 w-4" />
						Discord Community
					</Button>
					<Button variant="outline" size="sm">
						<FileText class="mr-2 h-4 w-4" />
						API Docs
					</Button>
				</div>
			</div>
		</Card>
	{/if}
</div>