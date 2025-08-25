<script lang="ts">
	import { page } from '$app/stores';
	import { cn } from '$lib/utils';
	import { 
		MessageSquare, 
		BookOpen, 
		Search, 
		Settings, 
		Brain, 
		Users,
		Home,
		FileText,
		Zap
	} from 'lucide-svelte';

	interface Props {
		open: boolean;
	}

	let { open = $bindable() }: Props = $props();

	const navigation = [
		{ name: 'Dashboard', href: '/', icon: Home },
		{ name: 'Chat', href: '/chat', icon: MessageSquare },
		{ name: 'Wiki', href: '/wiki', icon: BookOpen },
		{ name: 'Research', href: '/research', icon: Search },
		{ name: 'Models', href: '/models', icon: Brain },
		{ name: 'Agents', href: '/agents', icon: Users },
		{ name: 'Simple', href: '/simple', icon: Zap },
		{ name: 'Documentation', href: '/docs', icon: FileText },
	];

	function isActive(href: string): boolean {
		if (href === '/') {
			return $page.url.pathname === '/';
		}
		return $page.url.pathname.startsWith(href);
	}
</script>

<div 
	class={cn(
		'flex flex-col bg-japanese-card border-r border-japanese-border transition-all duration-300 ease-in-out shadow-custom',
		open ? 'w-64' : 'w-16',
		'fixed inset-y-0 left-0 z-50 lg:relative lg:z-0'
	)}
>
	<!-- Logo -->
	<div class="flex h-16 items-center justify-center border-b border-japanese-border px-4">
		{#if open}
			<h1 class="text-xl font-bold text-japanese-primary font-serif">Grantha</h1>
		{:else}
			<div class="flex h-8 w-8 items-center justify-center rounded bg-japanese-primary text-white shadow-custom">
				G
			</div>
		{/if}
	</div>

	<!-- Navigation -->
	<nav class="flex-1 space-y-1 p-4">
		{#each navigation as item}
			<a
				href={item.href}
				class={cn(
					'flex items-center rounded-lg px-3 py-2 text-sm font-medium transition-colors',
					isActive(item.href) 
						? 'bg-japanese-primary/10 text-japanese-primary border border-japanese-primary/20' 
						: 'text-japanese-muted hover:bg-japanese-primary/5 hover:text-japanese-primary',
					!open && 'justify-center'
				)}
				title={!open ? item.name : undefined}
			>
				{#if true}
					{@const IconComponent = item.icon}
					<IconComponent class="h-4 w-4" />
				{/if}
				{#if open}
					<span class="ml-3">{item.name}</span>
				{/if}
			</a>
		{/each}
	</nav>

	<!-- Settings -->
	<div class="border-t border-japanese-border p-4">
		<a
			href="/settings"
			class={cn(
				'flex items-center rounded-lg px-3 py-2 text-sm font-medium text-japanese-muted transition-colors hover:bg-japanese-primary/5 hover:text-japanese-primary',
				!open && 'justify-center'
			)}
			title={!open ? 'Settings' : undefined}
		>
			<Settings class="h-4 w-4" />
			{#if open}
				<span class="ml-3">Settings</span>
			{/if}
		</a>
	</div>
</div>