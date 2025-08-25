<script lang="ts">
	import { page } from '$app/stores';
	import { authActions } from '$stores/auth';
	import Button from '../ui/button.svelte';
	import ThemeToggle from '../ui/theme-toggle.svelte';
	import { Menu, LogOut, User, Settings } from 'lucide-svelte';
	import { type Writable } from 'svelte/store';

	interface Props {
		sidebarOpen: Writable<boolean>;
		onToggleSidebar?: () => void;
	}

	let { sidebarOpen, onToggleSidebar }: Props = $props();

	let showUserMenu = $state(false);

	function toggleSidebar() {
		sidebarOpen.update(open => !open);
		onToggleSidebar?.();
	}

	function handleLogout() {
		authActions.logout();
	}

	// Get page title from route
	const pageTitle = $derived(getPageTitle($page.route?.id));

	function getPageTitle(routeId: string | null): string {
		if (!routeId) return 'Grantha';
		
		const titleMap: Record<string, string> = {
			'/': 'Dashboard',
			'/chat': 'Chat',
			'/wiki': 'Wiki',
			'/research': 'Research',
			'/models': 'Models',
			'/agents': 'Agents',
			'/simple': 'Simple',
			'/docs': 'Documentation',
			'/settings': 'Settings'
		};
		
		return titleMap[routeId] || 'Grantha';
	}
</script>

<header class="flex h-16 items-center justify-between border-b border-japanese-border bg-japanese-card shadow-custom px-4">
	<!-- Left side -->
	<div class="flex items-center space-x-4">
		<Button
			variant="ghost"
			size="icon"
			onclick={toggleSidebar}
			class="lg:hidden"
		>
			<Menu class="h-4 w-4" />
		</Button>
		
		<div>
			<h1 class="text-lg font-semibold text-foreground font-serif">{pageTitle}</h1>
			<p class="text-sm text-japanese-muted">
				{new Date().toLocaleDateString('en-US', { 
					weekday: 'long', 
					year: 'numeric', 
					month: 'long', 
					day: 'numeric' 
				})}
			</p>
		</div>
	</div>

	<!-- Right side -->
	<div class="flex items-center space-x-2">
		<!-- Theme toggle -->
		<ThemeToggle />

		<!-- User menu -->
		<div class="relative">
			<Button
				variant="ghost"
				size="icon"
				onclick={() => showUserMenu = !showUserMenu}
				class="rounded-full"
			>
				<User class="h-4 w-4" />
			</Button>

			{#if showUserMenu}
				<div 
					class="absolute right-0 mt-2 w-48 rounded-md border border-japanese-border bg-japanese-card py-1 shadow-custom"
					role="menu"
				>
					<a
						href="/settings"
						class="flex items-center px-4 py-2 text-sm text-foreground hover:bg-japanese-primary/10"
						onclick={() => showUserMenu = false}
					>
						<Settings class="mr-3 h-4 w-4" />
						Settings
					</a>
					
					<hr class="my-1 border-japanese-border" />
					
					<button
						type="button"
						class="flex w-full items-center px-4 py-2 text-sm text-foreground hover:bg-japanese-primary/10"
						onclick={handleLogout}
					>
						<LogOut class="mr-3 h-4 w-4" />
						Sign Out
					</button>
				</div>
			{/if}
		</div>
	</div>
</header>

<!-- Click outside to close user menu -->
{#if showUserMenu}
	<div 
		class="fixed inset-0 z-10"
		onclick={() => showUserMenu = false}
		role="button"
		tabindex="0"
		onkeydown={(e) => e.key === 'Escape' && (showUserMenu = false)}
	></div>
{/if}