<script lang="ts">
	import { onMount } from 'svelte';
	import { 
		Users, 
		Play, 
		Pause, 
		Settings, 
		Activity,
		CheckCircle,
		AlertCircle,
		Clock
	} from 'lucide-svelte';
	import Button from '$lib/components/ui/button.svelte';
	import { cn } from '$lib/utils';

	interface Agent {
		id: string;
		name: string;
		description: string;
		capabilities: string[];
		status: 'active' | 'inactive' | 'busy';
		lastActive?: number;
	}

	// Mock agent data - would come from API
	const agents: Agent[] = [
		{
			id: 'fullstack-developer',
			name: 'Full-Stack Developer',
			description: 'Handles complete feature implementation and API development',
			capabilities: ['SvelteKit', 'TypeScript', 'API Design', 'Database Design'],
			status: 'active',
			lastActive: Date.now() - 300000
		},
		{
			id: 'api-designer',
			name: 'API Designer',
			description: 'Designs REST and GraphQL APIs with best practices',
			capabilities: ['REST Design', 'GraphQL', 'OpenAPI', 'Documentation'],
			status: 'active',
			lastActive: Date.now() - 600000
		},
		{
			id: 'websocket-engineer',
			name: 'WebSocket Engineer',
			description: 'Implements real-time features and WebSocket communication',
			capabilities: ['WebSocket', 'Real-time', 'Socket.IO', 'Event Handling'],
			status: 'busy',
			lastActive: Date.now() - 60000
		},
		{
			id: 'typescript-pro',
			name: 'TypeScript Pro',
			description: 'Ensures type safety and TypeScript best practices',
			capabilities: ['TypeScript', 'Type Safety', 'Generics', 'Code Quality'],
			status: 'active',
			lastActive: Date.now() - 120000
		},
		{
			id: 'ai-engineer',
			name: 'AI Engineer',
			description: 'Integrates AI models and builds ML pipelines',
			capabilities: ['LLM Integration', 'Model Selection', 'AI Workflows', 'Prompt Engineering'],
			status: 'active',
			lastActive: Date.now() - 180000
		},
		{
			id: 'security-auditor',
			name: 'Security Auditor',
			description: 'Reviews code for security vulnerabilities and implements fixes',
			capabilities: ['Security Audit', 'Vulnerability Assessment', 'OWASP', 'Penetration Testing'],
			status: 'inactive',
			lastActive: Date.now() - 3600000
		}
	];

	let selectedAgent = $state<Agent | null>(null);
	let filterStatus = $state<string>('all');

	const filteredAgents = $derived(() => {
		if (filterStatus === 'all') return agents as Agent[];
		return agents.filter(agent => agent.status === filterStatus) as Agent[];
	});

	function getStatusIcon(status: string) {
		switch (status) {
			case 'active': return CheckCircle;
			case 'busy': return Activity;
			case 'inactive': return Clock;
			default: return AlertCircle;
		}
	}

	function getStatusColor(status: string) {
		switch (status) {
			case 'active': return 'text-green-500';
			case 'busy': return 'text-orange-500';
			case 'inactive': return 'text-gray-500';
			default: return 'text-red-500';
		}
	}

	function formatLastActive(timestamp?: number): string {
		if (!timestamp) return 'Never';
		const diff = Date.now() - timestamp;
		const minutes = Math.floor(diff / 60000);
		if (minutes < 1) return 'Just now';
		if (minutes < 60) return `${minutes}m ago`;
		const hours = Math.floor(minutes / 60);
		if (hours < 24) return `${hours}h ago`;
		const days = Math.floor(hours / 24);
		return `${days}d ago`;
	}

	function toggleAgentStatus(agent: Agent) {
		// Mock toggle - would call API
		agent.status = agent.status === 'active' ? 'inactive' : 'active';
	}
</script>

<svelte:head>
	<title>Agents - Grantha</title>
</svelte:head>

<div class="space-y-8">
	<!-- Header -->
	<div class="text-center">
		<h1 class="text-4xl font-bold text-foreground mb-4">
			AI Agent Coordination
		</h1>
		<p class="text-lg text-muted-foreground max-w-2xl mx-auto">
			Manage and coordinate specialized AI agents for different development tasks.
			Each agent is optimized for specific workflows and capabilities.
		</p>
	</div>

	<!-- Stats -->
	<div class="grid grid-cols-1 md:grid-cols-4 gap-6">
		<div class="rounded-lg border bg-card p-6 text-center">
			<div class="text-2xl font-bold text-foreground">{agents.length}</div>
			<div class="text-sm text-muted-foreground">Total Agents</div>
		</div>
		<div class="rounded-lg border bg-card p-6 text-center">
			<div class="text-2xl font-bold text-green-500">
				{agents.filter(a => a.status === 'active').length}
			</div>
			<div class="text-sm text-muted-foreground">Active</div>
		</div>
		<div class="rounded-lg border bg-card p-6 text-center">
			<div class="text-2xl font-bold text-orange-500">
				{agents.filter(a => a.status === 'busy').length}
			</div>
			<div class="text-sm text-muted-foreground">Busy</div>
		</div>
		<div class="rounded-lg border bg-card p-6 text-center">
			<div class="text-2xl font-bold text-gray-500">
				{agents.filter(a => a.status === 'inactive').length}
			</div>
			<div class="text-sm text-muted-foreground">Inactive</div>
		</div>
	</div>

	<div class="grid grid-cols-1 lg:grid-cols-3 gap-8">
		<!-- Agent List -->
		<div class="lg:col-span-2">
			<!-- Filters -->
			<div class="flex items-center space-x-3 mb-6">
				<span class="text-sm font-medium text-muted-foreground">Filter:</span>
				{#each ['all', 'active', 'busy', 'inactive'] as status}
					<Button
						variant={filterStatus === status ? 'default' : 'ghost'}
						size="sm"
						onclick={() => filterStatus = status}
					>
						{status.charAt(0).toUpperCase() + status.slice(1)}
					</Button>
				{/each}
			</div>

			<!-- Agent Grid -->
			<div class="space-y-4">
				{#each filteredAgents() as agent (agent.id)}
					<div 
						class={cn(
							'rounded-lg border bg-card p-6 cursor-pointer transition-all hover:shadow-md',
							selectedAgent?.id === (agent as Agent).id && 'border-primary'
						)}
						role="button"
						tabindex="0"
						onclick={() => selectedAgent = agent as Agent}
						onkeydown={(e) => e.key === 'Enter' && (selectedAgent = agent as Agent)}
					>
						<div class="flex items-start justify-between mb-4">
							<div class="flex items-center space-x-3">
								<Users class="h-5 w-5 text-primary" />
								<div>
									<h3 class="font-semibold text-foreground">{agent.name}</h3>
									<p class="text-sm text-muted-foreground">{agent.description}</p>
								</div>
							</div>

							<div class="flex items-center space-x-2">
								<div class={cn('flex items-center space-x-1', getStatusColor(agent.status))}>
									{#if agent.status}
										{@const StatusIcon = getStatusIcon(agent.status)}
										<StatusIcon class="h-4 w-4" />
									{/if}
									<span class="text-sm font-medium capitalize">{agent.status}</span>
								</div>
								
								<Button
									size="icon"
									variant="ghost"
									class="h-8 w-8"
									onclick={(e) => {
										e.stopPropagation();
										toggleAgentStatus(agent as Agent);
									}}
									title={agent.status === 'active' ? 'Deactivate' : 'Activate'}
								>
									{#if agent.status === 'active'}
										<Pause class="h-4 w-4" />
									{:else}
										<Play class="h-4 w-4" />
									{/if}
								</Button>
							</div>
						</div>

						<div class="flex flex-wrap gap-2 mb-3">
							{#each agent.capabilities.slice(0, 3) as capability}
								<span class="px-2 py-1 rounded-full bg-accent text-accent-foreground text-xs">
									{capability}
								</span>
							{/each}
							{#if agent.capabilities.length > 3}
								<span class="px-2 py-1 rounded-full bg-muted text-muted-foreground text-xs">
									+{agent.capabilities.length - 3} more
								</span>
							{/if}
						</div>

						<div class="text-xs text-muted-foreground">
							Last active: {formatLastActive(agent.lastActive)}
						</div>
					</div>
				{/each}
			</div>
		</div>

		<!-- Agent Details -->
		<div class="lg:col-span-1">
			{#if selectedAgent}
				<div class="rounded-lg border bg-card p-6 sticky top-6">
					<div class="flex items-center justify-between mb-4">
						<h3 class="text-lg font-semibold text-foreground">Agent Details</h3>
						<Button size="icon" variant="ghost" class="h-8 w-8">
							<Settings class="h-4 w-4" />
						</Button>
					</div>

					<div class="space-y-4">
						<div>
							<h4 class="font-medium text-foreground mb-2">{selectedAgent.name}</h4>
							<p class="text-sm text-muted-foreground">{selectedAgent.description}</p>
						</div>

						<div>
							<h4 class="font-medium text-foreground mb-2">Status</h4>
							<div class={cn('flex items-center space-x-2', getStatusColor(selectedAgent.status))}>
								{#if selectedAgent.status}
									{@const StatusIcon = getStatusIcon(selectedAgent.status)}
									<StatusIcon class="h-4 w-4" />
								{/if}
								<span class="text-sm font-medium capitalize">{selectedAgent.status}</span>
							</div>
						</div>

						<div>
							<h4 class="font-medium text-foreground mb-2">Capabilities</h4>
							<div class="space-y-2">
								{#each selectedAgent.capabilities as capability}
									<div class="flex items-center space-x-2">
										<div class="w-2 h-2 bg-primary rounded-full"></div>
										<span class="text-sm text-muted-foreground">{capability}</span>
									</div>
								{/each}
							</div>
						</div>

						<div>
							<h4 class="font-medium text-foreground mb-2">Activity</h4>
							<p class="text-sm text-muted-foreground">
								Last active: {formatLastActive(selectedAgent.lastActive)}
							</p>
						</div>

						<div class="pt-4 space-y-2">
							<Button 
								class="w-full" 
								variant={selectedAgent.status === 'active' ? 'destructive' : 'default'}
								onclick={() => selectedAgent && toggleAgentStatus(selectedAgent)}
							>
								{#if selectedAgent.status === 'active'}
									<Pause class="mr-2 h-4 w-4" />
									Deactivate Agent
								{:else}
									<Play class="mr-2 h-4 w-4" />
									Activate Agent
								{/if}
							</Button>
							
							<Button variant="outline" class="w-full">
								<Settings class="mr-2 h-4 w-4" />
								Configure Agent
							</Button>
						</div>
					</div>
				</div>
			{:else}
				<div class="rounded-lg border bg-card p-6 text-center">
					<Users class="h-12 w-12 text-muted-foreground mx-auto mb-4" />
					<h3 class="text-lg font-semibold text-foreground mb-2">Select an Agent</h3>
					<p class="text-sm text-muted-foreground">
						Click on an agent to view detailed information and controls
					</p>
				</div>
			{/if}
		</div>
	</div>
</div>